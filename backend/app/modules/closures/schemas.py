from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class SolutionSummary(BaseModel):
    description: str
    resolved_by: UserSummary
    resolved_at: datetime


class ValidationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    ticket_id: UUID
    status: str
    expires_at: datetime
    days_remaining: int
    responded_at: datetime | None
    rejection_reason: str | None
    solution: SolutionSummary | None


class ValidationReject(BaseModel):
    rejection_reason: str = Field(min_length=1)


class TenantSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    auto_close_days: int
    updated_at: datetime
    updated_by: UUID | None


class TenantSettingsPatch(BaseModel):
    auto_close_days: int = Field(ge=1, le=90)
