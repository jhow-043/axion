from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class TicketCreate(BaseModel):
    type: Literal["industrial", "predial"]
    title: str
    description: str
    priority_id: UUID
    category_id: UUID | None = None
    equipment_id: UUID | None = None
    location_id: UUID | None = None
    team_id: UUID | None = None


class TicketTransition(BaseModel):
    to_status: Literal["in_progress", "pending", "resolved", "closed"]
    pending_reason_id: UUID | None = None
    solution_description: str | None = None


class TicketObserverAdd(BaseModel):
    user_id: UUID


class TicketCommentCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Conteúdo não pode ser vazio.")
        return v


class TicketCommentUpdate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Conteúdo não pode ser vazio.")
        return v


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    type: str
    title: str
    description: str
    priority_id: UUID
    status_id: UUID
    category_id: UUID | None
    equipment_id: UUID | None
    location_id: UUID | None
    team_id: UUID | None
    requester_id: UUID
    assignee_id: UUID | None
    assigned_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TicketResponse]


class TicketCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    author_id: UUID
    content: str
    created_at: datetime
    updated_at: datetime


class TicketCommentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TicketCommentResponse]


class TicketObserverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_id: UUID
    user_id: UUID
    added_at: datetime
