from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.closures.models import TenantSettings, Validation
from app.shared.base_repository import BaseRepository


class ValidationRepository(BaseRepository[Validation]):
    __model__ = Validation

    async def find_by_ticket(self, ticket_id: UUID) -> Validation | None:
        stmt = self._base_query().where(Validation.ticket_id == ticket_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_expired_pending(self, now: datetime) -> list[Validation]:
        stmt = (
            self._base_query()
            .where(Validation.status == "pending")
            .where(Validation.expires_at < now)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_lock(self, id: UUID) -> Validation | None:
        """SELECT FOR UPDATE to prevent double-close race condition."""
        stmt = self._base_query().where(Validation.id == id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class TenantSettingsRepository:
    """Not a BaseRepository subclass — tenant_settings has unique-per-tenant semantics."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def get(self) -> TenantSettings | None:
        stmt = select(TenantSettings).where(TenantSettings.tenant_id == self.tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_defaults(self) -> TenantSettings:
        existing = await self.get()
        if existing is not None:
            return existing
        obj = TenantSettings(tenant_id=self.tenant_id)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, data: dict) -> TenantSettings:
        obj = await self.get_or_create_defaults()
        for key, value in data.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
