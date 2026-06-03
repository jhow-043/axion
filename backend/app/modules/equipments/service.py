from __future__ import annotations

from uuid import UUID

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.equipments.repository import EquipmentRepository
from app.modules.equipments.schemas import (
    EquipmentCreate,
    EquipmentListResponse,
    EquipmentResponse,
    EquipmentTicketsResponse,
    EquipmentUpdate,
)
from app.modules.locations.repository import SectorRepository


class EquipmentService:
    def __init__(
        self,
        repo: EquipmentRepository,
        sector_repo: SectorRepository,
    ) -> None:
        self._repo = repo
        self._sector_repo = sector_repo

    async def create(self, data: EquipmentCreate, created_by: UUID) -> EquipmentResponse:
        if await self._repo.find_by_code(data.code) is not None:
            raise ConflictError("Código de equipamento já cadastrado neste tenant.")
        await self._validate_sector(data.sector_id)
        equipment = await self._repo.create(
            {
                "code": data.code,
                "name": data.name,
                "sector_id": data.sector_id,
                "manufacturer": data.manufacturer,
                "model": data.model,
                "serial_number": data.serial_number,
                "notes": data.notes,
                "created_by": created_by,
            }
        )
        return EquipmentResponse.model_validate(equipment)

    async def get(self, equipment_id: UUID) -> EquipmentResponse:
        equipment = await self._repo.get(equipment_id)
        if equipment is None:
            raise NotFoundError("Equipamento não encontrado.")
        return EquipmentResponse.model_validate(equipment)

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        sector_id: UUID | None = None,
        is_active: bool | None = None,
    ) -> EquipmentListResponse:
        offset = (page - 1) * page_size
        items = await self._repo.list_filtered(
            search=search,
            sector_id=sector_id,
            is_active=is_active,
            offset=offset,
            limit=page_size,
        )
        total = await self._repo.count_filtered(
            search=search, sector_id=sector_id, is_active=is_active
        )
        return EquipmentListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[EquipmentResponse.model_validate(e) for e in items],
        )

    async def update(self, equipment_id: UUID, data: EquipmentUpdate) -> EquipmentResponse:
        equipment = await self._repo.get(equipment_id)
        if equipment is None:
            raise NotFoundError("Equipamento não encontrado.")

        changes: dict = {}
        if data.code is not None and data.code != equipment.code:
            if await self._repo.find_by_code(data.code) is not None:
                raise ConflictError("Código de equipamento já cadastrado neste tenant.")
            changes["code"] = data.code
        if data.name is not None:
            changes["name"] = data.name
        if data.sector_id is not None and data.sector_id != equipment.sector_id:
            await self._validate_sector(data.sector_id)
            changes["sector_id"] = data.sector_id
        if "manufacturer" in data.model_fields_set:
            changes["manufacturer"] = data.manufacturer
        if "model" in data.model_fields_set:
            changes["model"] = data.model
        if "serial_number" in data.model_fields_set:
            changes["serial_number"] = data.serial_number
        if "notes" in data.model_fields_set:
            changes["notes"] = data.notes

        if changes:
            await self._repo.update(equipment_id, changes)
        return await self.get(equipment_id)

    async def deactivate(self, equipment_id: UUID) -> EquipmentResponse:
        equipment = await self._repo.get(equipment_id)
        if equipment is None:
            raise NotFoundError("Equipamento não encontrado.")
        if not equipment.is_active:
            raise BusinessRuleError("Equipamento já está inativo.")
        await self._repo.update(equipment_id, {"is_active": False})
        return await self.get(equipment_id)

    async def activate(self, equipment_id: UUID) -> EquipmentResponse:
        equipment = await self._repo.get(equipment_id)
        if equipment is None:
            raise NotFoundError("Equipamento não encontrado.")
        if equipment.is_active:
            raise BusinessRuleError("Equipamento já está ativo.")
        await self._repo.update(equipment_id, {"is_active": True})
        return await self.get(equipment_id)

    async def get_tickets(
        self, equipment_id: UUID, *, page: int, page_size: int
    ) -> EquipmentTicketsResponse:
        # Validates equipment existence (raises 404 cross-tenant — INV-02)
        equipment = await self._repo.get(equipment_id)
        if equipment is None:
            raise NotFoundError("Equipamento não encontrado.")
        # Ticket history populated by P09; returns empty list until tickets module is available
        return EquipmentTicketsResponse(total=0, page=page, page_size=page_size, items=[])

    async def _validate_sector(self, sector_id: UUID) -> None:
        sector = await self._sector_repo.get(sector_id)
        if sector is None:
            raise NotFoundError("Setor não encontrado.")
        # INV-02: sector_repo.get() returns None for cross-tenant IDs — no info leak
        if not sector.is_active:
            raise BusinessRuleError("Setor informado está inativo.")
