"""Mistral provider — the default, because its free API tier keeps us at $0.

Uses the OpenAI-compatible chat/completions endpoint via httpx (no SDK dep).
Docs: https://docs.mistral.ai/api/
"""

from __future__ import annotations

import httpx

from app.providers.base import LLMMessage, LLMProvider, LLMResponse, ProviderError

_API_URL = "https://api.mistral.ai/v1/chat/completions"


class MistralProvider(LLMProvider):
    name = "mistral"
    default_model = "mistral-small-latest"

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if not self.api_key:
            raise ProviderError("Mistral API key is not configured.")

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(_API_URL, json=payload, headers=headers)
        except httpx.HTTPError as exc:  # network-level failure
            raise ProviderError(f"Mistral request failed: {exc}") from exc

        if resp.status_code != 200:
            raise ProviderError(
                f"Mistral API error {resp.status_code}: {resp.text[:500]}"
            )

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ProviderError(f"Unexpected Mistral response shape: {data}") from exc

        return LLMResponse(content=content, model=data.get("model", self.model), raw=data)
