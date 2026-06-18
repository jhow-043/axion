from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_any_permission, require_module, require_permission
from app.core.permissions import ADMIN_CONFIG, EQUIPMENT_READ, TICKET_READ
from app.modules.locations.repository import LocationRepository, SectorRepository
from app.modules.locations.schemas import (
    LocationCreate,
    LocationListResponse,
    LocationResponse,
    LocationUpdate,
    SectorCreate,
    SectorListResponse,
    SectorResponse,
    SectorUpdate,
)
from app.modules.locations.service import LocationService, SectorService

sectors_router = APIRouter(prefix="/sectors", tags=["sectors"], dependencies=[Depends(require_module("manutencao"))])
locations_router = APIRouter(prefix="/locations", tags=["locations"], dependencies=[Depends(require_module("manutencao"))])


def _get_sector_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SectorService:
    return SectorService(SectorRepository(db, current_user.tenant_id))


def _get_location_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> LocationService:
    return LocationService(LocationRepository(db, current_user.tenant_id))


# ── Sectors ──────────────────────────────────────────────────────────────────


@sectors_router.get("", response_model=SectorListResponse)
async def list_sectors(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    is_active: bool | None = Query(default=None),
    service: SectorService = Depends(_get_sector_service),
    _: object = Depends(require_any_permission(EQUIPMENT_READ, ADMIN_CONFIG)),
) -> SectorListResponse:
    return await service.list(page=page, page_size=page_size, is_active=is_active)


@sectors_router.post("", response_model=SectorResponse, status_code=201)
async def create_sector(
    body: SectorCreate,
    service: SectorService = Depends(_get_sector_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> SectorResponse:
    return await service.create(body)


@sectors_router.get("/{sector_id}", response_model=SectorResponse)
async def get_sector(
    sector_id: UUID,
    service: SectorService = Depends(_get_sector_service),
    _: object = Depends(require_any_permission(EQUIPMENT_READ, ADMIN_CONFIG)),
) -> SectorResponse:
    return await service.get(sector_id)


@sectors_router.patch("/{sector_id}", response_model=SectorResponse)
async def update_sector(
    sector_id: UUID,
    body: SectorUpdate,
    service: SectorService = Depends(_get_sector_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> SectorResponse:
    return await service.update(sector_id, body)


@sectors_router.post("/{sector_id}/deactivate", response_model=SectorResponse)
async def deactivate_sector(
    sector_id: UUID,
    service: SectorService = Depends(_get_sector_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> SectorResponse:
    return await service.deactivate(sector_id)


@sectors_router.post("/{sector_id}/reactivate", response_model=SectorResponse)
async def reactivate_sector(
    sector_id: UUID,
    service: SectorService = Depends(_get_sector_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> SectorResponse:
    return await service.reactivate(sector_id)


# ── Locations ─────────────────────────────────────────────────────────────────


@locations_router.get("", response_model=LocationListResponse)
async def list_locations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    service: LocationService = Depends(_get_location_service),
    _: object = Depends(require_any_permission(TICKET_READ, ADMIN_CONFIG)),
) -> LocationListResponse:
    return await service.list(page=page, page_size=page_size, is_active=is_active)


@locations_router.post("", response_model=LocationResponse, status_code=201)
async def create_location(
    body: LocationCreate,
    service: LocationService = Depends(_get_location_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> LocationResponse:
    return await service.create(body)


@locations_router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    service: LocationService = Depends(_get_location_service),
    _: object = Depends(require_any_permission(TICKET_READ, ADMIN_CONFIG)),
) -> LocationResponse:
    return await service.get(location_id)


@locations_router.patch("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    body: LocationUpdate,
    service: LocationService = Depends(_get_location_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> LocationResponse:
    return await service.update(location_id, body)


@locations_router.post("/{location_id}/deactivate", response_model=LocationResponse)
async def deactivate_location(
    location_id: UUID,
    service: LocationService = Depends(_get_location_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> LocationResponse:
    return await service.deactivate(location_id)


@locations_router.post("/{location_id}/reactivate", response_model=LocationResponse)
async def reactivate_location(
    location_id: UUID,
    service: LocationService = Depends(_get_location_service),
    _: object = Depends(require_permission(ADMIN_CONFIG)),
) -> LocationResponse:
    return await service.reactivate(location_id)
