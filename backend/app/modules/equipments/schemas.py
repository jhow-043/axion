from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EquipmentCreate(BaseModel):
    # strict=True not used: sector_id UUID comes from JSON as string (Pydantic coerces str→UUID)
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=2, max_length=255)
    sector_id: UUID
    manufacturer: str | None = Field(default=None, max_length=255)
    model: str | None = Field(default=None, max_length=255)
    serial_number: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None)


class EquipmentUpdate(BaseModel):
    # strict=True not used: sector_id UUID comes from JSON as string

    code: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    sector_id: UUID | None = None
    manufacturer: str | None = Field(default=None, max_length=255)
    model: str | None = Field(default=None, max_length=255)
    serial_number: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class EquipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    sector_id: UUID
    is_active: bool
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    notes: str | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class EquipmentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[EquipmentResponse]


class TicketSummary(BaseModel):
    """Minimal ticket info returned by GET /equipments/{id}/tickets.
    Populated by P09; returns empty list until tickets module is available."""

    id: UUID
    title: str
    status_code: str
    priority_code: str
    created_at: datetime
    assignee_name: str | None


class EquipmentTicketsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TicketSummary]
