from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant

# Does NOT inherit BaseRepository — tenants table is global (no tenant_id).
# INV-01 applies only to domain data within a tenant; the tenants table is the top-level entity.


class TenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _active_stmt(self):
        return select(Tenant).where(Tenant.deleted_at.is_(None))

    async def list(self, *, offset: int = 0, limit: int = 20) -> list[Tenant]:
        stmt = self._active_stmt().order_by(Tenant.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        stmt = select(func.count()).select_from(Tenant).where(Tenant.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get(self, tenant_id: UUID) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.id == tenant_id, Tenant.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug, Tenant.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: dict[str, Any]) -> Tenant:
        tenant = Tenant(**data)
        self.session.add(tenant)
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant

    async def update(self, tenant_id: UUID, data: dict[str, Any]) -> Tenant | None:
        tenant = await self.get(tenant_id)
        if tenant is None:
            return None
        for key, value in data.items():
            setattr(tenant, key, value)
        await self.session.flush()
        await self.session.refresh(tenant)
        return tenant

    async def soft_delete(self, tenant_id: UUID) -> Tenant | None:
        tenant = await self.get(tenant_id)
        if tenant is None:
            return None
        tenant.deleted_at = datetime.utcnow()
        await self.session.flush()
        return tenant
