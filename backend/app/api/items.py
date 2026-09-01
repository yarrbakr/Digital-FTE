"""Item pipeline API: ingest → process → review → approve/reject → execute.

These endpoints back the dashboard (Phase 2). The manual ingest + process
endpoints also let us exercise the whole pipeline with no Gmail/Slack OAuth.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_session
from app.schemas import ItemCreate, ItemDetailOut, ItemOut, LogOut
from app.services import pipeline, stats

router = APIRouter(prefix="/api", tags=["pipeline"])


@router.post("/items", response_model=ItemOut, status_code=201)
def create_item(body: ItemCreate, session: Session = Depends(get_session)) -> models.Item:
    try:
        channel = models.Channel(body.channel.lower())
    except ValueError as exc:
        raise HTTPException(400, f"Unknown channel '{body.channel}'.") from exc
    return pipeline.ingest_item(
        session,
        channel=channel,
        external_id=body.external_id or f"manual-{uuid.uuid4().hex[:12]}",
        subject=body.subject,
        body=body.body,
        sender=body.sender,
    )


@router.get("/items", response_model=list[ItemOut])
def list_items(
    status: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[models.Item]:
    stmt = select(models.Item).order_by(models.Item.created_at.desc())
    if status:
        try:
            stmt = stmt.where(models.Item.status == models.ItemStatus(status.lower()))
        except ValueError as exc:
            raise HTTPException(400, f"Unknown status '{status}'.") from exc
    return list(session.scalars(stmt))


@router.get("/items/{item_id}", response_model=ItemDetailOut)
def get_item(item_id: int, session: Session = Depends(get_session)) -> models.Item:
    item = session.get(models.Item, item_id)
    if item is None:
        raise HTTPException(404, "Item not found.")
    return item


@router.post("/items/process")
def process_items(session: Session = Depends(get_session)) -> dict:
    """Analyze all NEW items and draft actions for them."""
    return pipeline.process_new_items(session)


@router.post("/items/{item_id}/approve", response_model=ItemOut)
def approve(item_id: int, session: Session = Depends(get_session)) -> models.Item:
    try:
        return pipeline.approve_item(session, item_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/items/{item_id}/reject", response_model=ItemOut)
def reject(item_id: int, session: Session = Depends(get_session)) -> models.Item:
    try:
        return pipeline.reject_item(session, item_id)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/items/execute")
def execute(session: Session = Depends(get_session)) -> dict:
    """Execute all APPROVED items on their channel."""
    return pipeline.execute_approved(session)


@router.get("/stats")
def get_stats(session: Session = Depends(get_session)) -> dict:
    """Aggregated metrics for the dashboard charts."""
    return stats.get_stats(session)


@router.get("/logs", response_model=list[LogOut])
def list_logs(
    limit: int = Query(default=50, le=500),
    session: Session = Depends(get_session),
) -> list[models.LogEntry]:
    stmt = select(models.LogEntry).order_by(models.LogEntry.created_at.desc()).limit(limit)
    return list(session.scalars(stmt))
