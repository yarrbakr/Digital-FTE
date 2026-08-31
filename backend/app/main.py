"""FastAPI entrypoint for Digital FTE.

Phase 0 exposes just enough to prove the foundation works: health, config
introspection, and a provider smoke-test that actually calls the configured
LLM (Mistral by default). The watch → draft → approve → act API arrives in
Phase 1, the dashboard consumes it in Phase 2.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app import __version__
from app.api.items import router as items_router
from app.config import get_settings
from app.db.database import init_db
from app.providers import ProviderError, available_providers, get_provider

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)

# Local dashboard (Next.js) runs on a different port → allow it in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": __version__}


@app.get("/api/config")
def config() -> dict:
    """Non-secret view of the active configuration (for the dashboard)."""
    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "api_key_set": bool(settings.llm_api_key),
        "poll_interval_seconds": settings.poll_interval_seconds,
        "database_url": settings.database_url,
    }


@app.get("/api/providers")
def providers() -> dict:
    return {"providers": available_providers(), "active": settings.llm_provider}


class PromptIn(BaseModel):
    prompt: str
    provider: str | None = None
    model: str | None = None


@app.post("/api/providers/test")
def provider_test(body: PromptIn) -> dict:
    """Smoke-test the configured provider with a one-off prompt."""
    from app.providers.base import LLMMessage

    provider_name = body.provider or settings.llm_provider
    model = body.model or settings.llm_model
    try:
        provider = get_provider(provider_name, settings.llm_api_key, model)
        resp = provider.complete([LLMMessage(role="user", content=body.prompt)])
    except ValueError as exc:  # unknown provider name
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProviderError as exc:  # auth / network / API failure
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {"provider": provider_name, "model": resp.model, "content": resp.content}
