from __future__ import annotations

from app.modules.hub.repository import ModuleRepository


class TestModuleRepositoryIsEnabled:
    async def test_returns_true_when_module_enabled_for_tenant(self, db_session):
        from app.modules.hub.seed import seed_manutencao_for_tenant
        from app.modules.tenants.models import Tenant

        tenant = Tenant(name="T1", slug="t-unit-1")
        db_session.add(tenant)
        await db_session.flush()
        await seed_manutencao_for_tenant(db_session, tenant.id)

        repo = ModuleRepository(db_session)
        assert await repo.is_enabled(tenant.id, "manutencao") is True

    async def test_returns_false_when_module_not_enabled(self, db_session):
        from app.modules.tenants.models import Tenant

        tenant = Tenant(name="T2", slug="t-unit-2")
        db_session.add(tenant)
        await db_session.flush()

        repo = ModuleRepository(db_session)
        assert await repo.is_enabled(tenant.id, "manutencao") is False

    async def test_returns_false_for_unknown_module_code(self, db_session):
        from app.modules.hub.seed import seed_manutencao_for_tenant
        from app.modules.tenants.models import Tenant

        tenant = Tenant(name="T3", slug="t-unit-3")
        db_session.add(tenant)
        await db_session.flush()
        await seed_manutencao_for_tenant(db_session, tenant.id)

        repo = ModuleRepository(db_session)
        assert await repo.is_enabled(tenant.id, "estoque") is False


class TestModuleRepositoryListEnabledForTenant:
    async def test_returns_codes_for_tenant(self, db_session):
        from app.modules.hub.seed import seed_manutencao_for_tenant
        from app.modules.tenants.models import Tenant

        tenant = Tenant(name="T4", slug="t-list-1")
        db_session.add(tenant)
        await db_session.flush()
        await seed_manutencao_for_tenant(db_session, tenant.id)

        repo = ModuleRepository(db_session)
        codes = await repo.list_enabled_for_tenant(tenant.id)
        assert "manutencao" in codes

    async def test_returns_empty_when_no_modules(self, db_session):
        from app.modules.tenants.models import Tenant

        tenant = Tenant(name="T5", slug="t-list-empty")
        db_session.add(tenant)
        await db_session.flush()

        repo = ModuleRepository(db_session)
        assert await repo.list_enabled_for_tenant(tenant.id) == []


class TestModuleRepositoryEnableForTenant:
    async def test_enables_module_for_tenant(self, db_session):
        from app.modules.hub.seed import seed_module_manutencao
        from app.modules.tenants.models import Tenant

        tenant = Tenant(name="T6", slug="t-enable-1")
        db_session.add(tenant)
        await db_session.flush()
        module = await seed_module_manutencao(db_session)

        repo = ModuleRepository(db_session)
        await repo.enable_for_tenant(tenant.id, module.id)

        assert await repo.is_enabled(tenant.id, "manutencao") is True

    async def test_enable_is_idempotent(self, db_session):
        from app.modules.hub.seed import seed_manutencao_for_tenant, seed_module_manutencao
        from app.modules.tenants.models import Tenant

        tenant = Tenant(name="T7", slug="t-enable-idem")
        db_session.add(tenant)
        await db_session.flush()
        module = await seed_module_manutencao(db_session)
        await seed_manutencao_for_tenant(db_session, tenant.id)

        repo = ModuleRepository(db_session)
        await repo.enable_for_tenant(tenant.id, module.id)

        codes = await repo.list_enabled_for_tenant(tenant.id)
        assert codes.count("manutencao") == 1


class TestSeedHelpers:
    async def test_seed_module_manutencao_is_idempotent(self, db_session):
        from app.modules.hub.seed import seed_module_manutencao

        m1 = await seed_module_manutencao(db_session)
        m2 = await seed_module_manutencao(db_session)
        assert m1.id == m2.id
        assert m1.code == "manutencao"

    async def test_seed_manutencao_for_tenant_is_idempotent(self, db_session):
        from app.modules.hub.seed import seed_manutencao_for_tenant
        from app.modules.tenants.models import Tenant

        tenant = Tenant(name="T8", slug="t-seed-idem")
        db_session.add(tenant)
        await db_session.flush()

        # Should not raise on second call
        await seed_manutencao_for_tenant(db_session, tenant.id)
        await seed_manutencao_for_tenant(db_session, tenant.id)

        repo = ModuleRepository(db_session)
        codes = await repo.list_enabled_for_tenant(tenant.id)
        assert codes.count("manutencao") == 1
