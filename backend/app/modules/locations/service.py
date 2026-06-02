from __future__ import annotations

from uuid import UUID

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
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


class SectorService:
    def __init__(self, repo: SectorRepository) -> None:
        self._repo = repo

    async def create(self, data: SectorCreate) -> SectorResponse:
        if await self._repo.find_by_name(data.name) is not None:
            raise ConflictError("Nome de setor já cadastrado neste tenant.")
        sector = await self._repo.create({"name": data.name, "description": data.description})
        return SectorResponse.model_validate(sector)

    async def get(self, sector_id: UUID) -> SectorResponse:
        sector = await self._repo.get(sector_id)
        if sector is None:
            raise NotFoundError("Setor não encontrado.")
        return SectorResponse.model_validate(sector)

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        is_active: bool | None = None,
    ) -> SectorListResponse:
        offset = (page - 1) * page_size
        items = await self._repo.list_filtered(is_active=is_active, offset=offset, limit=page_size)
        total = await self._repo.count_filtered(is_active=is_active)
        return SectorListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[SectorResponse.model_validate(s) for s in items],
        )

    async def update(self, sector_id: UUID, data: SectorUpdate) -> SectorResponse:
        sector = await self._repo.get(sector_id)
        if sector is None:
            raise NotFoundError("Setor não encontrado.")

        changes: dict = {}
        if data.name is not None and data.name != sector.name:
            if await self._repo.find_by_name(data.name) is not None:
                raise ConflictError("Nome de setor já cadastrado neste tenant.")
            changes["name"] = data.name
        if "description" in data.model_fields_set:
            changes["description"] = data.description

        if changes:
            await self._repo.update(sector_id, changes)
        return await self.get(sector_id)

    async def deactivate(self, sector_id: UUID) -> SectorResponse:
        sector = await self._repo.get(sector_id)
        if sector is None:
            raise NotFoundError("Setor não encontrado.")
        if not sector.is_active:
            raise BusinessRuleError("Setor já está inativo.")
        await self._repo.update(sector_id, {"is_active": False})
        return await self.get(sector_id)

    async def reactivate(self, sector_id: UUID) -> SectorResponse:
        sector = await self._repo.get(sector_id)
        if sector is None:
            raise NotFoundError("Setor não encontrado.")
        if sector.is_active:
            raise BusinessRuleError("Setor já está ativo.")
        await self._repo.update(sector_id, {"is_active": True})
        return await self.get(sector_id)


class LocationService:
    def __init__(self, repo: LocationRepository) -> None:
        self._repo = repo

    async def create(self, data: LocationCreate) -> LocationResponse:
        if await self._repo.find_by_name(data.name) is not None:
            raise ConflictError("Nome de local já cadastrado neste tenant.")
        location = await self._repo.create({"name": data.name, "description": data.description})
        return LocationResponse.model_validate(location)

    async def get(self, location_id: UUID) -> LocationResponse:
        location = await self._repo.get(location_id)
        if location is None:
            raise NotFoundError("Local não encontrado.")
        return LocationResponse.model_validate(location)

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        is_active: bool | None = None,
    ) -> LocationListResponse:
        offset = (page - 1) * page_size
        items = await self._repo.list_filtered(is_active=is_active, offset=offset, limit=page_size)
        total = await self._repo.count_filtered(is_active=is_active)
        return LocationListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[LocationResponse.model_validate(loc) for loc in items],
        )

    async def update(self, location_id: UUID, data: LocationUpdate) -> LocationResponse:
        location = await self._repo.get(location_id)
        if location is None:
            raise NotFoundError("Local não encontrado.")

        changes: dict = {}
        if data.name is not None and data.name != location.name:
            if await self._repo.find_by_name(data.name) is not None:
                raise ConflictError("Nome de local já cadastrado neste tenant.")
            changes["name"] = data.name
        if "description" in data.model_fields_set:
            changes["description"] = data.description

        if changes:
            await self._repo.update(location_id, changes)
        return await self.get(location_id)

    async def deactivate(self, location_id: UUID) -> LocationResponse:
        location = await self._repo.get(location_id)
        if location is None:
            raise NotFoundError("Local não encontrado.")
        if not location.is_active:
            raise BusinessRuleError("Local já está inativo.")
        await self._repo.update(location_id, {"is_active": False})
        return await self.get(location_id)

    async def reactivate(self, location_id: UUID) -> LocationResponse:
        location = await self._repo.get(location_id)
        if location is None:
            raise NotFoundError("Local não encontrado.")
        if location.is_active:
            raise BusinessRuleError("Local já está ativo.")
        await self._repo.update(location_id, {"is_active": True})
        return await self.get(location_id)
