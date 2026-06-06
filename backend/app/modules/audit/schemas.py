from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    actor: ActorSummary | None
    action: str
    entity_type: str
    entity_id: UUID
    before: dict | None
    after: dict | None
    ip_address: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AuditLogResponse]
