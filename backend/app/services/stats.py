"""Aggregated metrics for the dashboard's charts.

Kept simple (Python-side aggregation over the items table) — the dataset is
small for a self-host instance, and this keeps the query SQLite/Postgres
agnostic. Returns a single JSON-friendly dict the graph-first UI consumes.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models

_STATUSES = [s.value for s in models.ItemStatus]
_PRIORITIES = [p.value for p in models.Priority]
_CHANNELS = [c.value for c in models.Channel]


def get_stats(session: Session, days: int = 14) -> dict:
    items = list(session.scalars(select(models.Item)))

    by_status = Counter(i.status.value for i in items)
    by_priority = Counter(i.priority.value for i in items)
    by_channel = Counter(i.channel.value for i in items)

    # Decisions the human actually made (drives the approval-rate gauge).
    approved_like = by_status.get("approved", 0) + by_status.get("done", 0)
    rejected = by_status.get("rejected", 0)
    decided = approved_like + rejected
    approval_rate = round(approved_like / decided * 100) if decided else 0

    # Daily throughput for the last `days` days (by ingest date).
    today = datetime.now(timezone.utc).date()
    window = [today - timedelta(days=n) for n in range(days - 1, -1, -1)]
    per_day: Counter[str] = Counter()
    per_day_gmail: Counter[str] = Counter()
    per_day_slack: Counter[str] = Counter()
    for i in items:
        if not i.created_at:
            continue
        key = i.created_at.date().isoformat()
        per_day[key] += 1
        if i.channel == models.Channel.GMAIL:
            per_day_gmail[key] += 1
        elif i.channel == models.Channel.SLACK:
            per_day_slack[key] += 1

    throughput = [
        {
            "date": d.isoformat(),
            "label": d.strftime("%b %d"),
            "count": per_day.get(d.isoformat(), 0),
            "gmail": per_day_gmail.get(d.isoformat(), 0),
            "slack": per_day_slack.get(d.isoformat(), 0),
        }
        for d in window
    ]

    return {
        "total": len(items),
        "pending_approval": by_status.get("pending_approval", 0),
        "queued": by_status.get("approved", 0),
        "handled": by_status.get("done", 0),
        "new": by_status.get("new", 0),
        "failed": by_status.get("failed", 0),
        "approval_rate": approval_rate,
        "by_status": {s: by_status.get(s, 0) for s in _STATUSES},
        "by_priority": {p: by_priority.get(p, 0) for p in _PRIORITIES},
        "by_channel": {c: by_channel.get(c, 0) for c in _CHANNELS},
        "throughput": throughput,
    }
