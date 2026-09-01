"""Gmail watcher — reads unseen inbox mail over IMAP (stdlib only).

Uses IMAP + an app password (the $0, no-OAuth path chosen for the test
account). Fetches UNSEEN messages, ingests them as NEW items, and marks them
\\Seen so they aren't picked up twice. Message-ID is used as the dedup key.
"""

from __future__ import annotations

import email
import imaplib
from email.header import decode_header, make_header
from email.utils import parseaddr

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models
from app.services import pipeline

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993


def _decode(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw


def _extract_body(msg: email.message.Message) -> str:
    """Prefer text/plain; fall back to any text part."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(
                part.get("Content-Disposition", "")
            ):
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace").strip()
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace").strip()
    return str(msg.get_payload()).strip()


def check_credentials(email_addr: str, app_password: str) -> None:
    """Raise on bad credentials; used by the connect endpoint to validate."""
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    try:
        imap.login(email_addr, app_password)
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def fetch_new(email_addr: str, app_password: str, session: Session, limit: int = 10) -> int:
    """Ingest up to ``limit`` unseen emails. Returns the count ingested."""
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    ingested = 0
    try:
        imap.login(email_addr, app_password)
        imap.select("INBOX")
        typ, data = imap.search(None, "UNSEEN")
        if typ != "OK":
            return 0
        msg_nums = data[0].split()
        for num in msg_nums[-limit:]:
            typ, msg_data = imap.fetch(num, "(RFC822)")
            if typ != "OK" or not msg_data or not isinstance(msg_data[0], tuple):
                continue
            msg = email.message_from_bytes(msg_data[0][1])

            message_id = (msg.get("Message-ID") or f"imap-{num.decode()}").strip()
            exists = session.scalar(
                select(models.Item.id).where(models.Item.external_id == message_id)
            )
            if exists:
                imap.store(num, "+FLAGS", "\\Seen")
                continue

            subject = _decode(msg.get("Subject", "")) or "(no subject)"
            sender = parseaddr(msg.get("From", ""))[1] or _decode(msg.get("From", ""))
            body = _extract_body(msg)

            pipeline.ingest_item(
                session,
                channel=models.Channel.GMAIL,
                external_id=message_id,
                subject=subject,
                body=body,
                sender=sender,
            )
            imap.store(num, "+FLAGS", "\\Seen")
            ingested += 1
    finally:
        try:
            imap.logout()
        except Exception:
            pass
    return ingested
