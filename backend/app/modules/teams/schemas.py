from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class TeamUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class MemberAddRequest(BaseModel):
    user_id: UUID


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    added_at: datetime


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    is_active: bool
    member_count: int
    created_at: datetime
    updated_at: datetime


class TeamDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    is_active: bool
    members: list[MemberResponse]
    created_at: datetime
    updated_at: datetime


class TeamListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TeamResponse]
