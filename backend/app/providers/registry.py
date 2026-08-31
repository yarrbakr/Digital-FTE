"""Provider registry — the one place that maps a provider name to its class.

To add a provider (OpenAI, Claude, Ollama, …): implement ``LLMProvider`` and
add one line to ``_PROVIDERS``. Nothing else in the app changes.
"""

from __future__ import annotations

from app.providers.base import LLMProvider
from app.providers.mistral import MistralProvider

_PROVIDERS: dict[str, type[LLMProvider]] = {
    MistralProvider.name: MistralProvider,
    # "openai": OpenAIProvider,
    # "claude": ClaudeProvider,
    # "ollama": OllamaProvider,
}


def available_providers() -> list[dict[str, str]]:
    """List registered providers + their default model (for the dashboard)."""
    return [
        {"name": name, "default_model": cls.default_model}
        for name, cls in _PROVIDERS.items()
    ]


def get_provider(name: str, api_key: str, model: str | None = None) -> LLMProvider:
    """Instantiate a provider by name. Raises ValueError for unknown names."""
    cls = _PROVIDERS.get(name.lower())
    if cls is None:
        known = ", ".join(_PROVIDERS) or "(none)"
        raise ValueError(f"Unknown provider '{name}'. Available: {known}")
    return cls(api_key=api_key, model=model)
