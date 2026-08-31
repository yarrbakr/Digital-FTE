"""The provider abstraction — the contract every AI backend implements.

This is the seam that makes Digital FTE bring-your-own-provider: the pipeline
only ever talks to ``LLMProvider``. Adding OpenAI/Claude/Ollama = one new
subclass registered in ``registry.py`` — no pipeline changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class ProviderError(RuntimeError):
    """Raised when a provider call fails (auth, network, bad response)."""


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    raw: dict | None = field(default=None, repr=False)


class LLMProvider(ABC):
    """Base class for all AI providers.

    Subclasses set ``name`` and implement ``complete``. Keep implementations
    synchronous and dependency-light (httpx) so they run happily inside the
    in-process scheduler and are trivial to add.
    """

    name: str = "base"
    default_model: str = ""

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or self.default_model

    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Send a chat completion request and return the model's reply."""

    def health_check(self) -> bool:
        """Cheap sanity ping: does a tiny completion succeed?"""
        resp = self.complete(
            [LLMMessage(role="user", content="Reply with the single word: ok")],
            max_tokens=5,
        )
        return bool(resp.content)
