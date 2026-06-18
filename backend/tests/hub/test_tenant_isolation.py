from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.hub.repository import ModuleRepository
from app.modules.hub.seed import seed_manutencao_for_tenant
from app.modules.tenants.models import Tenant


class TestTenantIsolation:
    async def test_is_enabled_tenant_a_does_not_bleed_to_tenant_b(self, db_session: AsyncSession):
        """Module enabled for tenant A must not appear as enabled for tenant B."""
        tenant_a = Tenant(name="Iso A", slug="iso-a")
        tenant_b = Tenant(name="Iso B", slug="iso-b")
        db_session.add_all([tenant_a, tenant_b])
        await db_session.flush()

        await seed_manutencao_for_tenant(db_session, tenant_a.id)

        repo = ModuleRepository(db_session)
        assert await repo.is_enabled(tenant_a.id, "manutencao") is True
        assert await repo.is_enabled(tenant_b.id, "manutencao") is False

    async def test_list_enabled_for_tenant_returns_only_own_modules(self, db_session: AsyncSession):
        """list_enabled_for_tenant of tenant A must not contain data from tenant B."""
        tenant_a = Tenant(name="Iso A2", slug="iso-a2")
        tenant_b = Tenant(name="Iso B2", slug="iso-b2")
        db_session.add_all([tenant_a, tenant_b])
        await db_session.flush()

        await seed_manutencao_for_tenant(db_session, tenant_a.id)

        repo = ModuleRepository(db_session)
        codes_a = await repo.list_enabled_for_tenant(tenant_a.id)
        codes_b = await repo.list_enabled_for_tenant(tenant_b.id)

        assert "manutencao" in codes_a
        assert "manutencao" not in codes_b

    async def test_enable_for_tenant_b_does_not_affect_tenant_a(self, db_session: AsyncSession):
        """Enabling a module for tenant B after tenant A should not change tenant A's state."""
        tenant_a = Tenant(name="Iso A3", slug="iso-a3")
        tenant_b = Tenant(name="Iso B3", slug="iso-b3")
        db_session.add_all([tenant_a, tenant_b])
        await db_session.flush()

        # Only tenant A enabled initially
        await seed_manutencao_for_tenant(db_session, tenant_a.id)
        repo = ModuleRepository(db_session)
        assert await repo.is_enabled(tenant_b.id, "manutencao") is False

        # Now enable for tenant B
        await seed_manutencao_for_tenant(db_session, tenant_b.id)
        assert await repo.is_enabled(tenant_a.id, "manutencao") is True
        assert await repo.is_enabled(tenant_b.id, "manutencao") is True
