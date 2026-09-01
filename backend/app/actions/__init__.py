"""Channel executors + their registration into the pipeline's executor seam."""

from __future__ import annotations

from app.actions.gmail_send import send as gmail_send
from app.actions.slack_post import post as slack_post
from app.db import models
from app.services import executor


def register_all() -> None:
    """Wire real channel senders into the executor seam. Called at startup.

    Each sender self-checks its connection and simulates if unconfigured, so
    registering unconditionally is safe even before any channel is connected.
    """
    executor.register_executor(models.Channel.GMAIL, gmail_send)
    executor.register_executor(models.Channel.SLACK, slack_post)
