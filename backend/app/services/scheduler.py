"""In-process APScheduler loop — the automatic 'watches your inbox' heartbeat.

Every ``poll_interval_seconds`` it: (1) polls connected channels for new items,
(2) analyzes/drafts them via the AI provider. It deliberately does **not**
auto-execute — execution stays human-in-the-loop behind the approval step.

No Redis/Celery: a single BackgroundScheduler thread keeps the $0, one-process
self-host promise. If no channels are connected, the tick is a cheap no-op.
"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.db.database import SessionLocal
from app.services import pipeline, watch

_scheduler: BackgroundScheduler | None = None
_JOB_ID = "pipeline_tick"


def _tick() -> None:
    with SessionLocal() as session:
        try:
            watch.run_all(session)
        except Exception as exc:  # noqa: BLE001
            pipeline._log(session, "error", "scheduler", f"watch failed: {exc}")
            session.commit()
        try:
            pipeline.process_new_items(session)
        except Exception as exc:  # noqa: BLE001
            pipeline._log(session, "error", "scheduler", f"process failed: {exc}")
            session.commit()


def start() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    settings = get_settings()
    if not settings.scheduler_enabled:
        return
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _tick,
        "interval",
        seconds=settings.poll_interval_seconds,
        id=_JOB_ID,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()


def stop() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def is_running() -> bool:
    return _scheduler is not None and _scheduler.running
