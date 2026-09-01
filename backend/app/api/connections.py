"""Connections API — connect/validate/remove Gmail & Slack; run a poll now.

Secrets go in as plaintext over the (localhost) API and are stored encrypted;
they are never returned. Each connect endpoint validates the credentials
against the live service before saving, so the dashboard gets immediate,
honest feedback.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import get_session
from app.schemas import ConnectionOut, GmailConnectIn, SlackConnectIn
from app.services import connections as conn_service
from app.services import watch
from app.watchers import gmail as gmail_watcher
from app.watchers import slack as slack_watcher

router = APIRouter(prefix="/api", tags=["connections"])


@router.get("/connections", response_model=list[ConnectionOut])
def list_connections(session: Session = Depends(get_session)) -> list[models.Connection]:
    return conn_service.list_connections(session)


@router.post("/connections/gmail", response_model=ConnectionOut)
def connect_gmail(
    body: GmailConnectIn, session: Session = Depends(get_session)
) -> models.Connection:
    email_addr = body.email.strip()
    # Gmail shows app passwords in 4 groups of 4 — strip spaces before use.
    app_password = body.app_password.replace(" ", "").strip()
    try:
        gmail_watcher.check_credentials(email_addr, app_password)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Gmail login failed: {exc}") from exc

    return conn_service.save_connection(
        session,
        kind=models.ConnectionKind.GMAIL,
        name=email_addr,
        config={"email": email_addr, "app_password": app_password},
    )


@router.post("/connections/slack", response_model=ConnectionOut)
def connect_slack(
    body: SlackConnectIn, session: Session = Depends(get_session)
) -> models.Connection:
    bot_token = body.bot_token.strip()
    try:
        auth = slack_watcher.check_credentials(bot_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Slack auth failed: {exc}") from exc

    name = auth.get("team") or auth.get("url") or "Slack workspace"
    return conn_service.save_connection(
        session,
        kind=models.ConnectionKind.SLACK,
        name=name,
        config={"bot_token": bot_token},
    )


@router.delete("/connections/{kind}")
def delete_connection(kind: str, session: Session = Depends(get_session)) -> dict:
    try:
        conn_kind = models.ConnectionKind(kind.lower())
    except ValueError as exc:
        raise HTTPException(400, f"Unknown connection kind '{kind}'.") from exc
    removed = conn_service.delete_connection(session, conn_kind)
    if not removed:
        raise HTTPException(404, "Connection not found.")
    return {"deleted": kind}


@router.post("/watch/run")
def run_watch(session: Session = Depends(get_session)) -> dict:
    """Poll all connected channels for new items right now."""
    return watch.run_all(session)
