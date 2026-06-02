from __future__ import annotations

from sqlalchemy import func, select

from app.modules.locations.models import Location, Sector
from app.shared.base_repository import BaseRepository


class SectorRepository(BaseRepository[Sector]):
    __model__ = Sector

    async def find_by_name(self, name: str) -> Sector | None:
        stmt = self._base_query().where(Sector.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        *,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Sector]:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Sector.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit).order_by(Sector.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(self, *, is_active: bool | None = None) -> int:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Sector.is_active == is_active)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()


class LocationRepository(BaseRepository[Location]):
    __model__ = Location

    async def find_by_name(self, name: str) -> Location | None:
        stmt = self._base_query().where(Location.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        *,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Location]:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Location.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit).order_by(Location.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(self, *, is_active: bool | None = None) -> int:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Location.is_active == is_active)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()
