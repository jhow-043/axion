from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_module, require_permission
from app.core.permissions import EQUIPMENT_MANAGE, EQUIPMENT_READ
from app.modules.equipments.repository import EquipmentRepository
from app.modules.equipments.schemas import (
    EquipmentCreate,
    EquipmentListResponse,
    EquipmentResponse,
    EquipmentTicketsResponse,
    EquipmentUpdate,
)
from app.modules.equipments.service import EquipmentService
from app.modules.locations.repository import SectorRepository

router = APIRouter(prefix="/equipments", tags=["equipments"], dependencies=[Depends(require_module("manutencao"))])


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> EquipmentService:
    return EquipmentService(
        EquipmentRepository(db, current_user.tenant_id),
        SectorRepository(db, current_user.tenant_id),
    )


@router.get("", response_model=EquipmentListResponse)
async def list_equipments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None),
    sector_id: UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    service: EquipmentService = Depends(_get_service),
    _: object = Depends(require_permission(EQUIPMENT_READ)),
) -> EquipmentListResponse:
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sector_id=sector_id,
        is_active=is_active,
    )


@router.post("", response_model=EquipmentResponse, status_code=201)
async def create_equipment(
    body: EquipmentCreate,
    service: EquipmentService = Depends(_get_service),
    current_user=Depends(require_permission(EQUIPMENT_MANAGE)),
) -> EquipmentResponse:
    return await service.create(body, created_by=current_user.id)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: UUID,
    service: EquipmentService = Depends(_get_service),
    _: object = Depends(require_permission(EQUIPMENT_READ)),
) -> EquipmentResponse:
    return await service.get(equipment_id)


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: UUID,
    body: EquipmentUpdate,
    service: EquipmentService = Depends(_get_service),
    _: object = Depends(require_permission(EQUIPMENT_MANAGE)),
) -> EquipmentResponse:
    return await service.update(equipment_id, body)


@router.post("/{equipment_id}/deactivate", response_model=EquipmentResponse)
async def deactivate_equipment(
    equipment_id: UUID,
    service: EquipmentService = Depends(_get_service),
    _: object = Depends(require_permission(EQUIPMENT_MANAGE)),
) -> EquipmentResponse:
    return await service.deactivate(equipment_id)


@router.post("/{equipment_id}/activate", response_model=EquipmentResponse)
async def activate_equipment(
    equipment_id: UUID,
    service: EquipmentService = Depends(_get_service),
    _: object = Depends(require_permission(EQUIPMENT_MANAGE)),
) -> EquipmentResponse:
    return await service.activate(equipment_id)


@router.get("/{equipment_id}/tickets", response_model=EquipmentTicketsResponse)
async def list_equipment_tickets(
    equipment_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: EquipmentService = Depends(_get_service),
    _: object = Depends(require_permission(EQUIPMENT_READ)),
) -> EquipmentTicketsResponse:
    return await service.get_tickets(equipment_id, page=page, page_size=page_size)
