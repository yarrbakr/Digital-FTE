"""The AI brain: turn an incoming item into a prioritized, drafted action.

Provider-agnostic — it only uses the ``LLMProvider`` interface, so it works
with Mistral today and any future provider unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.providers.base import LLMMessage, LLMProvider, ProviderError

_VALID_PRIORITIES = {"high", "medium", "low"}
_VALID_ACTIONS = {"reply", "post", "none"}

_SYSTEM_PROMPT = """You are Digital FTE, an autonomous AI employee that triages \
incoming messages and drafts responses for a human to approve.

You will be given one message from a channel (email or slack). Do three things:
1. Assess PRIORITY as "high", "medium", or "low". Treat a message as "high" if it \
implies urgency, money, legal/contractual matters, or a hard deadline. These keywords \
strongly signal high priority: {keywords}.
2. Decide the ACTION: "reply" (draft a response), "post" (draft a message to send), \
or "none" (no response needed — FYI/newsletter/spam).
3. If the action is "reply" or "post", DRAFT the message content. Be concise, \
professional, and match the channel's tone (formal for email, conversational for slack). \
Do not invent facts you were not given. Leave placeholders like [DATE] if unknown.

Respond with ONLY a JSON object, no prose, no code fences, in exactly this shape:
{{"priority": "high|medium|low", "action_type": "reply|post|none", "draft": "<message text or empty>", "reasoning": "<one short sentence>"}}"""


@dataclass
class Analysis:
    priority: str
    action_type: str
    content: str
    reasoning: str


def _extract_json(text: str) -> dict:
    """Best-effort parse of a JSON object from a model reply."""
    text = text.strip()
    if text.startswith("```"):
        # strip ```json ... ``` fences
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"No JSON object found in model reply: {text[:200]}")
    return json.loads(text[start : end + 1])


def analyze(
    provider: LLMProvider,
    *,
    channel: str,
    subject: str,
    body: str,
    sender: str,
    priority_keywords: list[str],
) -> Analysis:
    """Run one item through the provider and return a structured Analysis."""
    user_content = (
        f"CHANNEL: {channel}\n"
        f"FROM: {sender}\n"
        f"SUBJECT: {subject}\n"
        f"MESSAGE:\n{body}"
    )
    messages = [
        LLMMessage(
            role="system",
            content=_SYSTEM_PROMPT.format(keywords=", ".join(priority_keywords)),
        ),
        LLMMessage(role="user", content=user_content),
    ]

    resp = provider.complete(messages, temperature=0.2, max_tokens=800)

    try:
        data = _extract_json(resp.content)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ProviderError(f"Could not parse analysis JSON: {exc}") from exc

    priority = str(data.get("priority", "medium")).lower()
    action_type = str(data.get("action_type", "reply")).lower()
    if priority not in _VALID_PRIORITIES:
        priority = "medium"
    if action_type not in _VALID_ACTIONS:
        action_type = "reply"

    return Analysis(
        priority=priority,
        action_type=action_type,
        content=str(data.get("draft", "")).strip(),
        reasoning=str(data.get("reasoning", "")).strip(),
    )
