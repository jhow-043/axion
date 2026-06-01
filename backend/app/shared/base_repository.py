from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(ABC, Generic[ModelT]):  # noqa: UP046
    """
    Tenant-scoped repository base. INV-01: every domain data access passes through here.
    INV-02: get() with a cross-tenant ID returns None → router raises 404.
    Subclasses declare: __model__ = MyModel
    """

    __model__: ClassVar[type[Any]]

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    def _base_query(self) -> Any:
        return select(self.__model__).where(self.__model__.tenant_id == self.tenant_id)

    async def get(self, id: UUID) -> ModelT | None:
        # 404 instead of 403 for cross-tenant IDs — does not reveal resource existence (ADR-0002)
        stmt = self._base_query().where(self.__model__.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 20) -> list[ModelT]:
        stmt = self._base_query().offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        stmt = (
            select(func.count())
            .select_from(self.__model__)
            .where(self.__model__.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, data: dict[str, Any]) -> ModelT:
        # INV-01: always override caller-supplied tenant_id to enforce isolation
        obj = self.__model__(**{**data, "tenant_id": self.tenant_id})
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id: UUID, data: dict[str, Any]) -> ModelT | None:
        obj = await self.get(id)
        if obj is None:
            return None
        for key, value in data.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: UUID) -> bool:
        obj = await self.get(id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        return True
