from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Priority ──────────────────────────────────────────────────────────────────


class PriorityCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    color: str | None = Field(default=None, max_length=20)
    order: int = Field(ge=1)


class PriorityUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    color: str | None = Field(default=None, max_length=20)
    order: int | None = Field(default=None, ge=1)


class PriorityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    code: str
    color: str | None
    order: int
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PriorityListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PriorityResponse]


# ── Status ────────────────────────────────────────────────────────────────────


class StatusUpdate(BaseModel):
    # extra="forbid" enforces INV-03: trying to send behavioral flags returns 422
    model_config = ConfigDict(strict=True, extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    order: int | None = Field(default=None, ge=1)


class StatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    code: str
    order: int
    requires_reason: bool
    requires_solution: bool
    is_terminal: bool
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StatusListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[StatusResponse]


# ── Category ──────────────────────────────────────────────────────────────────


class CategoryCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[CategoryResponse]


# ── PendingReason ─────────────────────────────────────────────────────────────


class PendingReasonCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class PendingReasonUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class PendingReasonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PendingReasonListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PendingReasonResponse]
