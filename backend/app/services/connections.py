"""CRUD for channel/provider connections (secrets encrypted) + a tiny KV store.

A ``Connection`` row holds one channel's credentials as an encrypted JSON blob
(``config_encrypted``). The dashboard never sees the secret back — only the
non-secret status. The KV helpers back small bits of watcher state (e.g. the
last-seen Slack timestamp per channel) in the ``settings`` table.
"""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import crypto


def save_connection(
    session: Session,
    *,
    kind: models.ConnectionKind,
    name: str,
    config: dict,
    status: str = "connected",
) -> models.Connection:
    """Create or update the single connection for a channel kind."""
    conn = session.scalar(
        select(models.Connection).where(models.Connection.kind == kind)
    )
    encrypted = crypto.encrypt(json.dumps(config))
    if conn is None:
        conn = models.Connection(kind=kind, name=name, config_encrypted=encrypted, status=status)
        session.add(conn)
    else:
        conn.name = name
        conn.config_encrypted = encrypted
        conn.status = status
    session.commit()
    session.refresh(conn)
    return conn


def get_config(session: Session, kind: models.ConnectionKind) -> dict | None:
    """Return the decrypted config for a channel, or None if not connected."""
    conn = session.scalar(
        select(models.Connection).where(models.Connection.kind == kind)
    )
    if conn is None or not conn.config_encrypted:
        return None
    try:
        return json.loads(crypto.decrypt(conn.config_encrypted))
    except Exception:
        return None


def list_connections(session: Session) -> list[models.Connection]:
    return list(session.scalars(select(models.Connection).order_by(models.Connection.kind)))


def set_status(session: Session, kind: models.ConnectionKind, status: str) -> None:
    conn = session.scalar(
        select(models.Connection).where(models.Connection.kind == kind)
    )
    if conn is not None:
        conn.status = status
        session.commit()


def delete_connection(session: Session, kind: models.ConnectionKind) -> bool:
    conn = session.scalar(
        select(models.Connection).where(models.Connection.kind == kind)
    )
    if conn is None:
        return False
    session.delete(conn)
    session.commit()
    return True


# --- tiny KV store (watcher cursors, etc.), backed by the settings table ---

def get_setting(session: Session, key: str) -> str | None:
    row = session.get(models.Setting, key)
    return row.value if row is not None else None


def set_setting(session: Session, key: str, value: str) -> None:
    row = session.get(models.Setting, key)
    if row is None:
        session.add(models.Setting(key=key, value=value))
    else:
        row.value = value
    session.commit()
