from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class TicketEventResponse(BaseModel):
    id: UUID
    type: str
    actor: ActorSummary | None
    payload: dict | None
    created_at: datetime


class TicketTimelineResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TicketEventResponse]
