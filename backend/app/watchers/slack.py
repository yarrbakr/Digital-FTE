"""Slack watcher — reads new messages from channels the bot belongs to.

Uses a bot token (xoxb-…). Invite the bot to a channel and it picks up new
human messages posted there, ingesting each as a NEW item. A per-channel
last-seen timestamp cursor (stored in the settings KV table) makes polling
incremental; bot/own/system messages are skipped.

external_id = "{channel_id}:{ts}" so the executor can reply in-thread later.
"""

from __future__ import annotations

from slack_sdk import WebClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import connections, pipeline


def check_credentials(bot_token: str) -> dict:
    """Validate the token via auth.test; returns the auth payload or raises."""
    return WebClient(token=bot_token).auth_test().data  # raises SlackApiError on bad token


def fetch_new(bot_token: str, session: Session, per_channel_limit: int = 20) -> int:
    client = WebClient(token=bot_token)
    auth = client.auth_test()
    bot_user_id = auth.get("user_id")

    channels = client.users_conversations(
        types="public_channel,private_channel", limit=200
    ).get("channels", [])

    ingested = 0
    for ch in channels:
        ch_id = ch["id"]
        ch_name = ch.get("name", ch_id)
        cursor_key = f"slack_last_ts:{ch_id}"
        last_ts = connections.get_setting(session, cursor_key)

        kwargs: dict = {"channel": ch_id, "limit": per_channel_limit}
        if last_ts:
            kwargs["oldest"] = last_ts
        messages = client.conversations_history(**kwargs).get("messages", [])

        newest_ts = last_ts
        for msg in sorted(messages, key=lambda m: m.get("ts", "0")):
            ts = msg.get("ts")
            if ts == last_ts:
                continue
            newest_ts = ts if (newest_ts is None or ts > newest_ts) else newest_ts

            # Skip bot/own/system messages — only act on human posts.
            if msg.get("bot_id") or msg.get("subtype") or msg.get("user") == bot_user_id:
                continue

            external_id = f"{ch_id}:{ts}"
            exists = session.scalar(
                select(models.Item.id).where(models.Item.external_id == external_id)
            )
            if exists:
                continue

            pipeline.ingest_item(
                session,
                channel=models.Channel.SLACK,
                external_id=external_id,
                subject=f"#{ch_name}",
                body=msg.get("text", ""),
                sender=msg.get("user", ""),
            )
            ingested += 1

        if newest_ts and newest_ts != last_ts:
            connections.set_setting(session, cursor_key, newest_ts)

    return ingested
