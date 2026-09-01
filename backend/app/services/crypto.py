"""Symmetric encryption for stored channel/provider credentials.

Credentials (Gmail app password, Slack bot token) are written to the DB
encrypted at rest with Fernet (AES-128-CBC + HMAC). The key comes from
``SECRET_KEY`` if set; otherwise a random key is generated once and cached in a
local ``.fte_key`` file next to the DB (git-ignored). This keeps the $0
self-host path zero-config while never storing secrets in plaintext.
"""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from cryptography.fernet import Fernet

from app.config import get_settings

# backend/.fte_key  (crypto.py is at backend/app/services/crypto.py)
_KEY_FILE = Path(__file__).resolve().parents[2] / ".fte_key"

_cipher: Fernet | None = None


def _load_or_create_key() -> bytes:
    settings = get_settings()
    if settings.secret_key:
        # Derive a stable urlsafe-base64 Fernet key from the user's secret.
        digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes().strip()

    key = Fernet.generate_key()
    _KEY_FILE.write_bytes(key)
    return key


def _get_cipher() -> Fernet:
    global _cipher
    if _cipher is None:
        _cipher = Fernet(_load_or_create_key())
    return _cipher


def encrypt(plaintext: str) -> str:
    return _get_cipher().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(token: str) -> str:
    return _get_cipher().decrypt(token.encode("ascii")).decode("utf-8")
