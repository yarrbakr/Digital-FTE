"""Gmail executor — sends an approved reply over SMTP (stdlib only).

Threads the reply to the original message via In-Reply-To/References (the
item's external_id is the original Message-ID). If Gmail isn't connected yet,
falls back to a simulated result so the demo pipeline still completes.
"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from email.utils import parseaddr

from app.db import models
from app.db.database import SessionLocal
from app.services import connections

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send(item: models.Item, draft: models.Draft) -> str:
    with SessionLocal() as session:
        cfg = connections.get_config(session, models.ConnectionKind.GMAIL)

    if not cfg:
        return f"[SIMULATED] Gmail not connected — would reply to '{item.sender}'."

    user = cfg["email"]
    password = cfg["app_password"]
    to_addr = parseaddr(item.sender)[1] or item.sender
    if not to_addr:
        raise RuntimeError("No recipient address on the item to reply to.")

    subject = item.subject or "(no subject)"
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    msg = MIMEText(draft.content, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    if item.external_id and item.external_id.startswith("<"):
        msg["In-Reply-To"] = item.external_id
        msg["References"] = item.external_id

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())

    return f"Sent email reply to {to_addr}."
