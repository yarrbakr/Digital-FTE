"""Application configuration, loaded from environment / .env.

Everything here has a sensible default so the app boots at $0 with zero
external services. The only value a user *must* supply to make the AI work is
an LLM API key (Mistral's free key by default).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    app_name: str = "Digital FTE"
    debug: bool = False

    # --- Database (embedded SQLite by default; swap to Postgres for SaaS) ---
    database_url: str = "sqlite:///./digital_fte.db"

    # --- AI provider (bring-your-own; Mistral free tier is the default) ---
    llm_provider: str = "mistral"
    llm_api_key: str = ""
    llm_model: str = "mistral-small-latest"

    # --- Secrets: key used to encrypt stored channel/provider credentials ---
    # Auto-generated on first run if left blank (see security note in db layer).
    secret_key: str = ""

    # --- Pipeline ---
    scheduler_enabled: bool = True
    poll_interval_seconds: int = 120
    priority_keywords: str = (
        "urgent,asap,immediately,important,deadline,critical,"
        "emergency,payment,invoice,contract,signature required"
    )

    @property
    def priority_keywords_list(self) -> list[str]:
        return [k.strip().lower() for k in self.priority_keywords.split(",") if k.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
