from __future__ import annotations

from sqlalchemy import func, select

from app.modules.catalog.models import Category, PendingReason, Priority, Status
from app.shared.base_repository import BaseRepository


class PriorityRepository(BaseRepository[Priority]):
    __model__ = Priority

    async def find_by_code(self, code: str) -> Priority | None:
        stmt = self._base_query().where(Priority.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self, *, is_active: bool | None = None, offset: int = 0, limit: int = 20
    ) -> list[Priority]:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Priority.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit).order_by(Priority.order)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(self, *, is_active: bool | None = None) -> int:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Priority.is_active == is_active)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()


class StatusRepository(BaseRepository[Status]):
    __model__ = Status

    async def find_by_code(self, code: str) -> Status | None:
        stmt = self._base_query().where(Status.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self, *, is_active: bool | None = None, offset: int = 0, limit: int = 20
    ) -> list[Status]:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Status.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit).order_by(Status.order)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(self, *, is_active: bool | None = None) -> int:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Status.is_active == is_active)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()


class CategoryRepository(BaseRepository[Category]):
    __model__ = Category

    async def find_by_name(self, name: str) -> Category | None:
        stmt = self._base_query().where(Category.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self, *, is_active: bool | None = None, offset: int = 0, limit: int = 20
    ) -> list[Category]:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Category.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit).order_by(Category.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(self, *, is_active: bool | None = None) -> int:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(Category.is_active == is_active)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()


class PendingReasonRepository(BaseRepository[PendingReason]):
    __model__ = PendingReason

    async def find_by_name(self, name: str) -> PendingReason | None:
        stmt = self._base_query().where(PendingReason.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self, *, is_active: bool | None = None, offset: int = 0, limit: int = 20
    ) -> list[PendingReason]:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(PendingReason.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit).order_by(PendingReason.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(self, *, is_active: bool | None = None) -> int:
        stmt = self._base_query()
        if is_active is not None:
            stmt = stmt.where(PendingReason.is_active == is_active)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()
