from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID | None
    event_type: str
    title: str
    body: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    unread_count: int
    items: list[NotificationResponse]


class PreferenceItem(BaseModel):
    event_type: str
    in_app_enabled: bool
    email_enabled: bool


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_type: str
    in_app_enabled: bool
    email_enabled: bool


class NotificationPreferencesPatch(BaseModel):
    preferences: list[PreferenceItem]


class NotificationPreferencesResponse(BaseModel):
    preferences: list[NotificationPreferenceResponse]
