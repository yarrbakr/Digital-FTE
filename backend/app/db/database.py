"""SQLAlchemy engine + session, backed by SQLite by default.

The DB is the single source of truth (replaces the old Obsidian vault). The
same code targets Postgres for the SaaS door by swapping ``DATABASE_URL``.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# check_same_thread=False lets the APScheduler worker and API share SQLite.
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_session() -> Iterator[Session]:
    """FastAPI dependency: yields a session and always closes it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create all tables. Called on app startup."""
    # Import models so they register on Base.metadata before create_all.
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
