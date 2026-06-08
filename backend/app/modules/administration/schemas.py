from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool
    is_system: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyRowResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool
    is_system: bool
    created_at: datetime
    user_count: int
    ticket_count: int
    plan: str | None = None


class GlobalDashboardResponse(BaseModel):
    total_companies: int
    active_companies: int
    suspended_companies: int
    total_users: int
    total_tickets: int
    companies: list[CompanyRowResponse]
    page: int
    page_size: int
    total_company_pages: int


class TenantCreate(BaseModel):
    name: str
    slug: str
    admin_name: str
    admin_email: str
    admin_password: str

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug deve conter apenas letras minúsculas, números e hífens.")
        return v

    @field_validator("admin_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter ao menos 8 caracteres.")
        return v


class TenantUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_active: bool | None = None

    @field_validator("slug")
    @classmethod
    def slug_format(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug deve conter apenas letras minúsculas, números e hífens.")
        return v


class TenantListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TenantResponse]
