from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.locations.schemas import (
    LocationCreate,
    LocationUpdate,
    SectorCreate,
    SectorUpdate,
)
from app.modules.locations.service import LocationService, SectorService


def _make_sector(*, is_active: bool = True, name: str = "TI") -> MagicMock:
    s = MagicMock()
    s.id = uuid.uuid4()
    s.name = name
    s.description = None
    s.is_active = is_active
    s.tenant_id = uuid.uuid4()
    return s


def _make_location(*, is_active: bool = True, name: str = "Galpão A") -> MagicMock:
    loc = MagicMock()
    loc.id = uuid.uuid4()
    loc.name = name
    loc.description = None
    loc.is_active = is_active
    loc.tenant_id = uuid.uuid4()
    return loc


def _sector_service(*, sector=None, find_by_name=None) -> SectorService:
    repo = AsyncMock()
    repo.find_by_name.return_value = find_by_name
    repo.get.return_value = sector
    repo.create.return_value = sector
    repo.update.return_value = sector
    return SectorService(repo)


def _location_service(*, location=None, find_by_name=None) -> LocationService:
    repo = AsyncMock()
    repo.find_by_name.return_value = find_by_name
    repo.get.return_value = location
    repo.create.return_value = location
    repo.update.return_value = location
    return LocationService(repo)


class TestSectorServiceUniqueNameRule:
    async def test_duplicate_name_raises_conflict(self):
        existing = _make_sector()
        service = _sector_service(sector=existing, find_by_name=existing)
        with pytest.raises(ConflictError):
            await service.create(SectorCreate(name="TI", description=None))

    async def test_unique_name_creates_sector(self):
        sector = _make_sector()
        service = _sector_service(sector=sector, find_by_name=None)
        result = await service.create(SectorCreate(name="TI", description=None))
        assert result.name == "TI"

    async def test_update_to_existing_name_raises_conflict(self):
        current = _make_sector(name="Mecânica")
        other = _make_sector(name="Elétrica")
        service = _sector_service(sector=current, find_by_name=other)
        with pytest.raises(ConflictError):
            await service.update(current.id, SectorUpdate(name="Elétrica"))


class TestSectorServiceDeactivation:
    async def test_deactivate_sets_is_active_false(self):
        sector = _make_sector(is_active=True)
        service = _sector_service(sector=sector)
        await service.deactivate(sector.id)
        service._repo.update.assert_awaited_once_with(sector.id, {"is_active": False})

    async def test_deactivate_already_inactive_raises(self):
        sector = _make_sector(is_active=False)
        service = _sector_service(sector=sector)
        with pytest.raises(BusinessRuleError):
            await service.deactivate(sector.id)

    async def test_reactivate_inactive_sector(self):
        sector = _make_sector(is_active=False)
        service = _sector_service(sector=sector)
        await service.reactivate(sector.id)
        service._repo.update.assert_awaited_once_with(sector.id, {"is_active": True})

    async def test_reactivate_active_raises(self):
        sector = _make_sector(is_active=True)
        service = _sector_service(sector=sector)
        with pytest.raises(BusinessRuleError):
            await service.reactivate(sector.id)


class TestSectorServiceNotFound:
    async def test_get_unknown_raises_not_found(self):
        service = _sector_service(sector=None)
        with pytest.raises(NotFoundError):
            await service.get(uuid.uuid4())

    async def test_deactivate_unknown_raises_not_found(self):
        service = _sector_service(sector=None)
        with pytest.raises(NotFoundError):
            await service.deactivate(uuid.uuid4())

    async def test_update_unknown_raises_not_found(self):
        service = _sector_service(sector=None)
        with pytest.raises(NotFoundError):
            await service.update(uuid.uuid4(), SectorUpdate(name="XX"))


class TestLocationServiceUniqueNameRule:
    async def test_duplicate_name_raises_conflict(self):
        existing = _make_location()
        service = _location_service(location=existing, find_by_name=existing)
        with pytest.raises(ConflictError):
            await service.create(LocationCreate(name="Sala 101", description=None))

    async def test_unique_name_creates_location(self):
        loc = _make_location()
        service = _location_service(location=loc, find_by_name=None)
        result = await service.create(LocationCreate(name="Galpão A", description=None))
        assert result.name == "Galpão A"

    async def test_update_to_existing_name_raises_conflict(self):
        current = _make_location(name="Galpão A")
        other = _make_location(name="Galpão B")
        service = _location_service(location=current, find_by_name=other)
        with pytest.raises(ConflictError):
            await service.update(current.id, LocationUpdate(name="Galpão B"))


class TestLocationServiceDeactivation:
    async def test_deactivate_sets_is_active_false(self):
        loc = _make_location(is_active=True)
        service = _location_service(location=loc)
        await service.deactivate(loc.id)
        service._repo.update.assert_awaited_once_with(loc.id, {"is_active": False})

    async def test_deactivate_already_inactive_raises(self):
        loc = _make_location(is_active=False)
        service = _location_service(location=loc)
        with pytest.raises(BusinessRuleError):
            await service.deactivate(loc.id)

    async def test_reactivate_inactive_location(self):
        loc = _make_location(is_active=False)
        service = _location_service(location=loc)
        await service.reactivate(loc.id)
        service._repo.update.assert_awaited_once_with(loc.id, {"is_active": True})

    async def test_reactivate_active_raises(self):
        loc = _make_location(is_active=True)
        service = _location_service(location=loc)
        with pytest.raises(BusinessRuleError):
            await service.reactivate(loc.id)


class TestLocationServiceNotFound:
    async def test_get_unknown_raises_not_found(self):
        service = _location_service(location=None)
        with pytest.raises(NotFoundError):
            await service.get(uuid.uuid4())

    async def test_deactivate_unknown_raises_not_found(self):
        service = _location_service(location=None)
        with pytest.raises(NotFoundError):
            await service.deactivate(uuid.uuid4())

    async def test_update_unknown_raises_not_found(self):
        service = _location_service(location=None)
        with pytest.raises(NotFoundError):
            await service.update(uuid.uuid4(), LocationUpdate(name="XX"))
