from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select

from app.modules.equipments.models import Equipment
from app.shared.base_repository import BaseRepository


class EquipmentRepository(BaseRepository[Equipment]):
    __model__ = Equipment

    async def find_by_code(self, code: str) -> Equipment | None:
        stmt = self._base_query().where(Equipment.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        *,
        search: str | None = None,
        sector_id: UUID | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Equipment]:
        stmt = self._base_query()
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Equipment.name.ilike(pattern), Equipment.code.ilike(pattern)))
        if sector_id is not None:
            stmt = stmt.where(Equipment.sector_id == sector_id)
        if is_active is not None:
            stmt = stmt.where(Equipment.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit).order_by(Equipment.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        search: str | None = None,
        sector_id: UUID | None = None,
        is_active: bool | None = None,
    ) -> int:
        stmt = self._base_query()
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Equipment.name.ilike(pattern), Equipment.code.ilike(pattern)))
        if sector_id is not None:
            stmt = stmt.where(Equipment.sector_id == sector_id)
        if is_active is not None:
            stmt = stmt.where(Equipment.is_active == is_active)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()
