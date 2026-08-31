"""Helper to build the active LLM provider from settings."""

from __future__ import annotations

from app.config import get_settings
from app.providers import LLMProvider, get_provider


def get_active_provider() -> LLMProvider:
    s = get_settings()
    return get_provider(s.llm_provider, s.llm_api_key, s.llm_model)
