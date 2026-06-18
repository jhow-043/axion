from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None
    icon: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TenantModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    module_id: UUID
    enabled_at: datetime


# ── P21: Platform admin module management ─────────────────────────────────────

class ModuleCatalogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    icon: str | None
    is_active: bool


class TenantEnabledModule(BaseModel):
    module_id: UUID
    module_code: str
    enabled_at: datetime


class TenantModulesResponse(BaseModel):
    catalog: list[ModuleCatalogItem]
    enabled: list[TenantEnabledModule]


class EnableModuleRequest(BaseModel):
    module_id: UUID
