"""Runs all connected watchers in one pass (called by the API and scheduler)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import models
from app.services import connections
from app.services.pipeline import _log
from app.watchers import gmail as gmail_watcher
from app.watchers import slack as slack_watcher


def run_all(session: Session) -> dict:
    """Poll every connected channel for new items. Returns per-channel counts."""
    results: dict[str, int | str] = {}

    gmail_cfg = connections.get_config(session, models.ConnectionKind.GMAIL)
    if gmail_cfg:
        try:
            results["gmail"] = gmail_watcher.fetch_new(
                gmail_cfg["email"], gmail_cfg["app_password"], session
            )
        except Exception as exc:  # noqa: BLE001 — surface channel errors, keep polling others
            results["gmail_error"] = str(exc)
            _log(session, "error", "watcher.gmail", f"Poll failed: {exc}")
            connections.set_status(session, models.ConnectionKind.GMAIL, "error")
            session.commit()

    slack_cfg = connections.get_config(session, models.ConnectionKind.SLACK)
    if slack_cfg:
        try:
            results["slack"] = slack_watcher.fetch_new(slack_cfg["bot_token"], session)
        except Exception as exc:  # noqa: BLE001
            results["slack_error"] = str(exc)
            _log(session, "error", "watcher.slack", f"Poll failed: {exc}")
            connections.set_status(session, models.ConnectionKind.SLACK, "error")
            session.commit()

    return results
