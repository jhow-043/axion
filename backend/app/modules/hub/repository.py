from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.hub.models import Module, TenantModule


class ModuleRepository:
    """Global module queries. Not a BaseRepository subclass — modules table has no tenant_id
    and tenant_modules is accessed cross-tenant by super-admin (ADR-0006)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_catalog(self) -> list[Module]:
        stmt = select(Module).where(Module.is_active.is_(True)).order_by(Module.sort_order)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Module | None:
        stmt = select(Module).where(Module.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_enabled(self, tenant_id: UUID, code: str) -> bool:
        stmt = (
            select(TenantModule.id)
            .join(Module, Module.id == TenantModule.module_id)
            .where(TenantModule.tenant_id == tenant_id, Module.code == code)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_enabled_for_tenant(self, tenant_id: UUID) -> list[str]:
        stmt = (
            select(Module.code)
            .join(TenantModule, TenantModule.module_id == Module.id)
            .where(TenantModule.tenant_id == tenant_id, Module.is_active.is_(True))
            .order_by(Module.sort_order)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def enable_for_tenant(self, tenant_id: UUID, module_id: UUID) -> None:
        """Inserts a TenantModule row. Idempotent — no-op when already enabled."""
        existing = await self.session.execute(
            select(TenantModule.id).where(
                TenantModule.tenant_id == tenant_id,
                TenantModule.module_id == module_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            self.session.add(TenantModule(tenant_id=tenant_id, module_id=module_id))
            await self.session.flush()
