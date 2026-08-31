"""ORM models — the core entities of the watch → draft → approve → act pipeline.

These replace the Obsidian folders: an ``Item``'s ``status`` field is what used
to be "which folder the .md file lives in" (Needs_Action / Approved / Done / …).
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Channel(str, enum.Enum):
    GMAIL = "gmail"
    SLACK = "slack"


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ItemStatus(str, enum.Enum):
    NEW = "new"                          # ingested by a watcher, not yet analyzed
    DRAFTED = "drafted"                  # AI produced a draft
    PENDING_APPROVAL = "pending_approval"  # awaiting human review
    APPROVED = "approved"                # human approved; queued to execute
    REJECTED = "rejected"                # human rejected
    DONE = "done"                        # action executed successfully
    FAILED = "failed"                    # action execution failed


class ConnectionKind(str, enum.Enum):
    GMAIL = "gmail"
    SLACK = "slack"
    PROVIDER = "provider"


class Item(Base):
    """A unit of work pulled from a channel (an email, a Slack message)."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[Channel] = mapped_column(Enum(Channel), index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(1024), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    sender: Mapped[str] = mapped_column(String(512), default="")
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.MEDIUM)
    status: Mapped[ItemStatus] = mapped_column(
        Enum(ItemStatus), default=ItemStatus.NEW, index=True
    )
    received_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )

    drafts: Mapped[list[Draft]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class Draft(Base):
    """The AI-produced action proposed for an Item, pending human approval."""

    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64), default="")
    model: Mapped[str] = mapped_column(String(128), default="")
    action_type: Mapped[str] = mapped_column(String(64), default="reply")
    content: Mapped[str] = mapped_column(Text, default="")
    reasoning: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    item: Mapped[Item] = relationship(back_populates="drafts")


class Connection(Base):
    """A configured channel/provider credential (secrets stored encrypted)."""

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[ConnectionKind] = mapped_column(Enum(ConnectionKind), index=True)
    name: Mapped[str] = mapped_column(String(128), default="")
    config_encrypted: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="disconnected")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )


class Setting(Base):
    """Key/value app configuration editable from the dashboard."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )


class LogEntry(Base):
    """Pipeline / audit events (replaces the Obsidian /Logs files)."""

    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    level: Mapped[str] = mapped_column(String(16), default="info", index=True)
    source: Mapped[str] = mapped_column(String(64), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    item_id: Mapped[int | None] = mapped_column(
        ForeignKey("items.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
