"""Executes an approved draft on its channel.

Channel adapters (real Gmail send / Slack post) register here. Until they're
wired (they need OAuth/bot tokens), execution is *simulated* so the full
pipeline is demoable at $0 with no external credentials. The seam is the same,
so dropping in the real senders later changes nothing upstream.
"""

from __future__ import annotations

from collections.abc import Callable

from app.db import models

# channel -> callable(item, draft) -> str (human-readable result)
_EXECUTORS: dict[models.Channel, Callable[[models.Item, models.Draft], str]] = {}


def register_executor(
    channel: models.Channel, fn: Callable[[models.Item, models.Draft], str]
) -> None:
    _EXECUTORS[channel] = fn


def _simulated(item: models.Item, draft: models.Draft) -> str:
    return (
        f"[SIMULATED] Would {draft.action_type} on {item.channel.value} "
        f"to '{item.sender}': {draft.content[:80]}..."
    )


def execute(item: models.Item, draft: models.Draft) -> str:
    """Run the registered executor for the item's channel (or simulate)."""
    fn = _EXECUTORS.get(item.channel, _simulated)
    return fn(item, draft)
