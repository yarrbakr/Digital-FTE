"""The orchestrator: moves items through watch → draft → approve → act.

Each function is a small, transactional step so it can be driven by the API
(manual buttons in the dashboard) *and* by the scheduler (automatic ticks).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import models
from app.providers.base import ProviderError
from app.services import executor
from app.services.ai import get_active_provider
from app.services.analyzer import analyze


def _log(session: Session, level: str, source: str, message: str, item_id: int | None = None) -> None:
    session.add(
        models.LogEntry(level=level, source=source, message=message, item_id=item_id)
    )


def ingest_item(
    session: Session,
    *,
    channel: models.Channel,
    external_id: str,
    subject: str,
    body: str,
    sender: str,
) -> models.Item:
    """Create a NEW item (used by watchers and by the manual test endpoint)."""
    item = models.Item(
        channel=channel,
        external_id=external_id,
        subject=subject,
        body=body,
        sender=sender,
        status=models.ItemStatus.NEW,
    )
    session.add(item)
    _log(session, "info", "ingest", f"New {channel.value} item: {subject!r}")
    session.commit()
    session.refresh(item)
    return item


def process_new_items(session: Session, limit: int = 20) -> dict:
    """Analyze NEW items → create a Draft → move to PENDING_APPROVAL."""
    settings = get_settings()
    provider = get_active_provider()
    keywords = settings.priority_keywords_list

    items = list(
        session.scalars(
            select(models.Item)
            .where(models.Item.status == models.ItemStatus.NEW)
            .limit(limit)
        )
    )

    processed, errors = 0, 0
    for item in items:
        try:
            result = analyze(
                provider,
                channel=item.channel.value,
                subject=item.subject,
                body=item.body,
                sender=item.sender,
                priority_keywords=keywords,
            )
        except ProviderError as exc:
            errors += 1
            _log(session, "error", "analyzer", f"Analysis failed: {exc}", item.id)
            continue

        item.priority = models.Priority(result.priority)
        if result.action_type == "none" or not result.content:
            # Nothing to send — skip the human queue, mark done.
            item.status = models.ItemStatus.DONE
            _log(session, "info", "analyzer", "No action needed; marked done.", item.id)
        else:
            draft = models.Draft(
                item_id=item.id,
                provider=provider.name,
                model=provider.model,
                action_type=result.action_type,
                content=result.content,
                reasoning=result.reasoning,
            )
            session.add(draft)
            item.status = models.ItemStatus.PENDING_APPROVAL
            _log(
                session,
                "info",
                "analyzer",
                f"Drafted {result.action_type} (priority={result.priority}).",
                item.id,
            )
        processed += 1

    session.commit()
    return {"processed": processed, "errors": errors, "found": len(items)}


def approve_item(session: Session, item_id: int) -> models.Item:
    item = _require_item(session, item_id)
    if item.status != models.ItemStatus.PENDING_APPROVAL:
        raise ValueError(f"Item {item_id} is not pending approval (status={item.status.value}).")
    item.status = models.ItemStatus.APPROVED
    _log(session, "info", "approval", "Human approved.", item.id)
    session.commit()
    session.refresh(item)
    return item


def reject_item(session: Session, item_id: int) -> models.Item:
    item = _require_item(session, item_id)
    if item.status != models.ItemStatus.PENDING_APPROVAL:
        raise ValueError(f"Item {item_id} is not pending approval (status={item.status.value}).")
    item.status = models.ItemStatus.REJECTED
    _log(session, "info", "approval", "Human rejected.", item.id)
    session.commit()
    session.refresh(item)
    return item


def execute_approved(session: Session, limit: int = 20) -> dict:
    """Execute APPROVED items on their channel → DONE (or FAILED)."""
    items = list(
        session.scalars(
            select(models.Item)
            .where(models.Item.status == models.ItemStatus.APPROVED)
            .limit(limit)
        )
    )

    done, failed = 0, 0
    for item in items:
        draft = item.drafts[-1] if item.drafts else None
        if draft is None:
            item.status = models.ItemStatus.FAILED
            failed += 1
            _log(session, "error", "executor", "No draft to execute.", item.id)
            continue
        try:
            result = executor.execute(item, draft)
            item.status = models.ItemStatus.DONE
            done += 1
            _log(session, "info", "executor", result, item.id)
        except Exception as exc:  # channel-level failure
            item.status = models.ItemStatus.FAILED
            failed += 1
            _log(session, "error", "executor", f"Execution failed: {exc}", item.id)

    session.commit()
    return {"done": done, "failed": failed, "found": len(items)}


def _require_item(session: Session, item_id: int) -> models.Item:
    item = session.get(models.Item, item_id)
    if item is None:
        raise LookupError(f"Item {item_id} not found.")
    return item
