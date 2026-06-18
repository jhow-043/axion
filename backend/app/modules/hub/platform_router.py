from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_system_admin
from app.modules.administration.repository import TenantRepository
from app.modules.hub.repository import ModuleRepository
from app.modules.hub.schemas import (
    EnableModuleRequest,
    ModuleCatalogItem,
    TenantModulesResponse,
)
from app.modules.hub.service import PlatformModuleService

router = APIRouter(prefix="/admin/platform", tags=["platform-modules"])


def _get_service(db: AsyncSession = Depends(get_db)) -> PlatformModuleService:
    return PlatformModuleService(
        module_repo=ModuleRepository(db),
        tenant_repo=TenantRepository(db),
    )


@router.get("/modules", response_model=list[ModuleCatalogItem])
async def list_module_catalog(
    service: PlatformModuleService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> list[ModuleCatalogItem]:
    return await service.list_catalog()


@router.get("/tenants/{tenant_id}/modules", response_model=TenantModulesResponse)
async def get_tenant_modules(
    tenant_id: UUID,
    service: PlatformModuleService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> TenantModulesResponse:
    return await service.get_tenant_modules(tenant_id)


@router.post("/tenants/{tenant_id}/modules", status_code=status.HTTP_200_OK)
async def enable_tenant_module(
    tenant_id: UUID,
    body: EnableModuleRequest,
    service: PlatformModuleService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> dict:
    await service.enable_module(tenant_id, body.module_id)
    return {"status": "enabled"}


@router.delete(
    "/tenants/{tenant_id}/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_tenant_module(
    tenant_id: UUID,
    module_id: UUID,
    service: PlatformModuleService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> None:
    await service.revoke_module(tenant_id, module_id)
