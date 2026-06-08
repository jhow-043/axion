from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_system_admin
from app.modules.administration.repository import TenantRepository
from app.modules.administration.schemas import (
    GlobalDashboardResponse,
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantUpdate,
)
from app.modules.administration.service import AdminService
from app.modules.audit.service import build_audit_service

router = APIRouter(prefix="/admin/tenants", tags=["administration"])


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AdminService:
    audit_svc = build_audit_service(db, current_user.tenant_id)
    return AdminService(
        tenant_repo=TenantRepository(db),
        db=db,
        audit_svc=audit_svc,
        actor_id=current_user.id,
    )


# NOTE: /dashboard must be declared before /{tenant_id} so FastAPI does not
# attempt to parse "dashboard" as a UUID path parameter.
@router.get("/dashboard", response_model=GlobalDashboardResponse)
async def get_dashboard(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: AdminService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> GlobalDashboardResponse:
    return await service.get_dashboard(page=page, page_size=page_size)


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: AdminService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> TenantListResponse:
    return await service.list_tenants(page=page, page_size=page_size)


@router.post("", response_model=TenantResponse, status_code=201)
async def provision_tenant(
    body: TenantCreate,
    service: AdminService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> TenantResponse:
    return await service.provision_tenant(body)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    service: AdminService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> TenantResponse:
    return await service.get_tenant(tenant_id)


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    body: TenantUpdate,
    service: AdminService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> TenantResponse:
    return await service.update_tenant(tenant_id, body)


@router.post("/{tenant_id}/activate", response_model=TenantResponse)
async def activate_tenant(
    tenant_id: UUID,
    service: AdminService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> TenantResponse:
    return await service.activate_tenant(tenant_id)


@router.post("/{tenant_id}/deactivate", response_model=TenantResponse)
async def deactivate_tenant(
    tenant_id: UUID,
    service: AdminService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> TenantResponse:
    return await service.deactivate_tenant(tenant_id)


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: UUID,
    service: AdminService = Depends(_get_service),
    _: None = Depends(require_system_admin()),
) -> None:
    await service.delete_tenant(tenant_id)
