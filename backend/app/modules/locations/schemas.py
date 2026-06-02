from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SectorCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class SectorUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class SectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SectorListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SectorResponse]


class LocationCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class LocationUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LocationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[LocationResponse]
