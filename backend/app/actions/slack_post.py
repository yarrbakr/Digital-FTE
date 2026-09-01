"""Slack executor — posts an approved reply, in-thread, via the bot token.

The item's external_id is "{channel_id}:{ts}"; we post back to that channel and
thread. If Slack isn't connected, falls back to a simulated result.
"""

from __future__ import annotations

from slack_sdk import WebClient

from app.db import models
from app.db.database import SessionLocal
from app.services import connections


def post(item: models.Item, draft: models.Draft) -> str:
    with SessionLocal() as session:
        cfg = connections.get_config(session, models.ConnectionKind.SLACK)

    if not cfg:
        return f"[SIMULATED] Slack not connected — would post in '{item.subject}'."

    channel_id, _, thread_ts = item.external_id.partition(":")
    client = WebClient(token=cfg["bot_token"])
    client.chat_postMessage(
        channel=channel_id,
        text=draft.content,
        thread_ts=thread_ts or None,
    )
    return f"Posted Slack reply in {item.subject or channel_id}."
