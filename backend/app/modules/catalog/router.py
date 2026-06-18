from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_module, require_permission
from app.core.permissions import ADMIN_CONFIG, TICKET_READ, TICKET_TRANSITION
from app.modules.catalog.repository import (
    CategoryRepository,
    PendingReasonRepository,
    PriorityRepository,
    StatusRepository,
)
from app.modules.catalog.schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
    PendingReasonCreate,
    PendingReasonListResponse,
    PendingReasonResponse,
    PendingReasonUpdate,
    PriorityCreate,
    PriorityListResponse,
    PriorityResponse,
    PriorityUpdate,
    StatusListResponse,
    StatusResponse,
    StatusUpdate,
)
from app.modules.catalog.service import (
    CategoryService,
    PendingReasonService,
    PriorityService,
    StatusService,
)

catalog_router = APIRouter(prefix="/catalog", tags=["catalog"], dependencies=[Depends(require_module("manutencao"))])


def _priority_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> PriorityService:
    return PriorityService(PriorityRepository(db, current_user.tenant_id))


def _status_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> StatusService:
    return StatusService(StatusRepository(db, current_user.tenant_id))


def _category_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> CategoryService:
    return CategoryService(CategoryRepository(db, current_user.tenant_id))


def _pending_reason_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> PendingReasonService:
    return PendingReasonService(PendingReasonRepository(db, current_user.tenant_id))


# ── Priorities ────────────────────────────────────────────────────────────────


@catalog_router.get("/priorities", response_model=PriorityListResponse)
async def list_priorities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    service: PriorityService = Depends(_priority_service),
    _: object = Depends(require_permission(TICKET_READ)),
) -> PriorityListResponse:
    return await service.list(page=page, page_size=page_size, is_active=is_active)


@catalog_router.post("/priorities", response_model=PriorityResponse, status_code=201)
async def create_priority(
    body: PriorityCreate,
    service: PriorityService = Depends(_priority_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> PriorityResponse:
    return await service.create(body)


@catalog_router.patch("/priorities/{priority_id}", response_model=PriorityResponse)
async def update_priority(
    priority_id: UUID,
    body: PriorityUpdate,
    service: PriorityService = Depends(_priority_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> PriorityResponse:
    return await service.update(priority_id, body)


@catalog_router.post("/priorities/{priority_id}/deactivate", response_model=PriorityResponse)
async def deactivate_priority(
    priority_id: UUID,
    service: PriorityService = Depends(_priority_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> PriorityResponse:
    return await service.deactivate(priority_id)


# ── Statuses ──────────────────────────────────────────────────────────────────


@catalog_router.get("/statuses", response_model=StatusListResponse)
async def list_statuses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    service: StatusService = Depends(_status_service),
    _: object = Depends(require_permission(TICKET_READ)),
) -> StatusListResponse:
    return await service.list(page=page, page_size=page_size, is_active=is_active)


@catalog_router.patch("/statuses/{status_id}", response_model=StatusResponse)
async def update_status(
    status_id: UUID,
    body: StatusUpdate,
    service: StatusService = Depends(_status_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> StatusResponse:
    return await service.update(status_id, body)


# ── Categories ────────────────────────────────────────────────────────────────


@catalog_router.get("/categories", response_model=CategoryListResponse)
async def list_categories(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    service: CategoryService = Depends(_category_service),
    _: object = Depends(require_permission(TICKET_READ)),
) -> CategoryListResponse:
    return await service.list(page=page, page_size=page_size, is_active=is_active)


@catalog_router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    body: CategoryCreate,
    service: CategoryService = Depends(_category_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> CategoryResponse:
    return await service.create(body)


@catalog_router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    body: CategoryUpdate,
    service: CategoryService = Depends(_category_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> CategoryResponse:
    return await service.update(category_id, body)


@catalog_router.post("/categories/{category_id}/deactivate", response_model=CategoryResponse)
async def deactivate_category(
    category_id: UUID,
    service: CategoryService = Depends(_category_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> CategoryResponse:
    return await service.deactivate(category_id)


# ── Pending Reasons ───────────────────────────────────────────────────────────


@catalog_router.get("/pending-reasons", response_model=PendingReasonListResponse)
async def list_pending_reasons(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    service: PendingReasonService = Depends(_pending_reason_service),
    _: object = Depends(require_permission(TICKET_TRANSITION)),
) -> PendingReasonListResponse:
    return await service.list(page=page, page_size=page_size, is_active=is_active)


@catalog_router.post("/pending-reasons", response_model=PendingReasonResponse, status_code=201)
async def create_pending_reason(
    body: PendingReasonCreate,
    service: PendingReasonService = Depends(_pending_reason_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> PendingReasonResponse:
    return await service.create(body)


@catalog_router.patch("/pending-reasons/{reason_id}", response_model=PendingReasonResponse)
async def update_pending_reason(
    reason_id: UUID,
    body: PendingReasonUpdate,
    service: PendingReasonService = Depends(_pending_reason_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> PendingReasonResponse:
    return await service.update(reason_id, body)


@catalog_router.post(
    "/pending-reasons/{reason_id}/deactivate", response_model=PendingReasonResponse
)
async def deactivate_pending_reason(
    reason_id: UUID,
    service: PendingReasonService = Depends(_pending_reason_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> PendingReasonResponse:
    return await service.deactivate(reason_id)
