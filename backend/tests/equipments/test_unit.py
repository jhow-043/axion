from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.equipments.schemas import EquipmentCreate, EquipmentUpdate
from app.modules.equipments.service import EquipmentService


def _make_service(
    *,
    find_by_code=None,
    get_equipment=None,
    get_sector=None,
) -> EquipmentService:
    repo = AsyncMock()
    sector_repo = AsyncMock()
    repo.find_by_code.return_value = find_by_code
    repo.get.return_value = get_equipment
    sector_repo.get.return_value = get_sector
    return EquipmentService(repo, sector_repo)


class TestCreateEquipment:
    async def test_duplicate_code_raises_conflict(self):
        existing = AsyncMock(id=uuid4(), code="EQ-001")
        svc = _make_service(find_by_code=existing)
        with pytest.raises(ConflictError):
            await svc.create(
                EquipmentCreate(code="EQ-001", name="Motor", sector_id=uuid4()),
                created_by=uuid4(),
            )

    async def test_inactive_sector_raises_business_rule(self):
        inactive_sector = AsyncMock(id=uuid4(), is_active=False)
        svc = _make_service(find_by_code=None, get_sector=inactive_sector)
        with pytest.raises(BusinessRuleError, match="inativo"):
            await svc.create(
                EquipmentCreate(code="EQ-002", name="Bomba", sector_id=uuid4()),
                created_by=uuid4(),
            )

    async def test_sector_not_found_raises_not_found(self):
        svc = _make_service(find_by_code=None, get_sector=None)
        with pytest.raises(NotFoundError):
            await svc.create(
                EquipmentCreate(code="EQ-003", name="Compressor", sector_id=uuid4()),
                created_by=uuid4(),
            )


class TestDeactivateEquipment:
    async def test_deactivate_already_inactive_raises(self):
        equipment = AsyncMock(is_active=False)
        svc = _make_service(get_equipment=equipment)
        with pytest.raises(BusinessRuleError, match="já está inativo"):
            await svc.deactivate(uuid4())

    async def test_deactivate_not_found_raises(self):
        svc = _make_service(get_equipment=None)
        with pytest.raises(NotFoundError):
            await svc.deactivate(uuid4())


class TestActivateEquipment:
    async def test_activate_already_active_raises(self):
        equipment = AsyncMock(is_active=True)
        svc = _make_service(get_equipment=equipment)
        with pytest.raises(BusinessRuleError, match="já está ativo"):
            await svc.activate(uuid4())

    async def test_activate_not_found_raises(self):
        svc = _make_service(get_equipment=None)
        with pytest.raises(NotFoundError):
            await svc.activate(uuid4())


class TestUpdateEquipment:
    async def test_update_with_duplicate_code_raises_conflict(self):
        equipment = AsyncMock(id=uuid4(), code="OLD-001", sector_id=uuid4())
        other = AsyncMock(id=uuid4(), code="NEW-001")
        svc = _make_service(find_by_code=other, get_equipment=equipment)
        with pytest.raises(ConflictError):
            await svc.update(
                equipment.id,
                EquipmentUpdate(code="NEW-001"),
            )

    async def test_update_sector_to_inactive_raises(self):
        equipment = AsyncMock(id=uuid4(), code="EQ-001", sector_id=uuid4())
        inactive_sector = AsyncMock(is_active=False)
        repo = AsyncMock()
        repo.find_by_code.return_value = None
        repo.get.return_value = equipment
        sector_repo = AsyncMock()
        new_sector_id = uuid4()
        sector_repo.get.return_value = inactive_sector
        svc = EquipmentService(repo, sector_repo)
        with pytest.raises(BusinessRuleError, match="inativo"):
            await svc.update(equipment.id, EquipmentUpdate(sector_id=new_sector_id))

    async def test_update_not_found_raises(self):
        svc = _make_service(get_equipment=None)
        with pytest.raises(NotFoundError):
            await svc.update(uuid4(), EquipmentUpdate(name="Novo Nome"))
