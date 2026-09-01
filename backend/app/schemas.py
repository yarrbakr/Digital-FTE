"""Pydantic request/response models for the API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemCreate(BaseModel):
    channel: str = "gmail"       # "gmail" | "slack"
    subject: str = ""
    body: str
    sender: str = ""
    external_id: str | None = None


class DraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    provider: str
    model: str
    action_type: str
    content: str
    reasoning: str
    created_at: datetime


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel: str
    external_id: str
    subject: str
    body: str
    sender: str
    priority: str
    status: str
    received_at: datetime
    created_at: datetime


class ItemDetailOut(ItemOut):
    drafts: list[DraftOut] = []


class DraftUpdate(BaseModel):
    content: str


class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    level: str
    source: str
    message: str
    item_id: int | None
    created_at: datetime


class GmailConnectIn(BaseModel):
    email: str
    app_password: str


class SlackConnectIn(BaseModel):
    bot_token: str


class ConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    name: str
    status: str
    updated_at: datetime
