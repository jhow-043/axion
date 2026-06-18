from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.hub.models import Module, TenantModule

_MANUTENCAO_CODE = "manutencao"


async def seed_module_manutencao(session: AsyncSession) -> Module:
    """Ensures the 'manutencao' module exists in the global catalogue. Idempotent."""
    stmt = select(Module).where(Module.code == _MANUTENCAO_CODE)
    result = await session.execute(stmt)
    module = result.scalar_one_or_none()
    if module is None:
        module = Module(
            code=_MANUTENCAO_CODE,
            name="Gestão de Manutenção",
            description="Abertura, acompanhamento e encerramento de chamados de manutenção.",
            icon="Wrench",
            sort_order=0,
        )
        session.add(module)
        await session.flush()
        await session.refresh(module)
    return module


async def seed_manutencao_for_tenant(session: AsyncSession, tenant_id: UUID) -> None:
    """Enables the 'manutencao' module for a specific tenant. Idempotent."""
    module = await seed_module_manutencao(session)

    existing = await session.execute(
        select(TenantModule.id).where(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_id == module.id,
        )
    )
    if existing.scalar_one_or_none() is None:
        session.add(TenantModule(tenant_id=tenant_id, module_id=module.id))
        await session.flush()
