from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SlaPolicyCreate(BaseModel):
    ticket_type: Literal["industrial", "predial", "all"]
    priority_id: UUID
    team_id: UUID | None = None
    attendance_minutes: int = Field(gt=0)
    resolution_minutes: int = Field(gt=0)
    alert_threshold_pct: int = Field(default=80, ge=1, le=100)


class SlaPolicyPatch(BaseModel):
    attendance_minutes: int | None = Field(default=None, gt=0)
    resolution_minutes: int | None = Field(default=None, gt=0)
    alert_threshold_pct: int | None = Field(default=None, ge=1, le=100)


class SlaPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    ticket_type: str
    priority_id: UUID
    team_id: UUID | None
    attendance_minutes: int
    resolution_minutes: int
    alert_threshold_pct: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SlaPolicyListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SlaPolicyResponse]


class SlaAttendanceDetail(BaseModel):
    due_at: datetime | None
    status: str
    met_at: datetime | None


class SlaResolutionDetail(BaseModel):
    due_at: datetime | None
    status: str
    met_at: datetime | None
    elapsed_minutes: int | None
    remaining_minutes: int | None
    paused_minutes: int


class SlaTicketResponse(BaseModel):
    """Response for GET /tickets/{id}/sla."""

    policy_id: UUID
    attendance: SlaAttendanceDetail
    resolution: SlaResolutionDetail
