from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant
from tests.tenants._models import SampleItemRepository


class TestTenantIsolation:
    """CA: Teste de isolamento — query de um tenant nunca retorna dados do outro."""

    async def test_tenant_a_cannot_get_tenant_b_record(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        repo_b = SampleItemRepository(session=db_session, tenant_id=tenant_b.id)
        item_b = await repo_b.create({"name": "B exclusive"})

        repo_a = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        result = await repo_a.get(item_b.id)

        assert result is None

    async def test_tenant_b_cannot_get_tenant_a_record(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        repo_a = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        item_a = await repo_a.create({"name": "A exclusive"})

        repo_b = SampleItemRepository(session=db_session, tenant_id=tenant_b.id)
        result = await repo_b.get(item_a.id)

        assert result is None

    async def test_list_returns_only_own_tenant_items(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        repo_a = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        repo_b = SampleItemRepository(session=db_session, tenant_id=tenant_b.id)

        item_a = await repo_a.create({"name": "for A"})
        item_b = await repo_b.create({"name": "for B"})

        items_a = await repo_a.list()
        items_b = await repo_b.list()

        ids_a = {i.id for i in items_a}
        ids_b = {i.id for i in items_b}

        assert item_a.id in ids_a
        assert item_b.id not in ids_a
        assert item_b.id in ids_b
        assert item_a.id not in ids_b

    async def test_count_counts_only_own_tenant_items(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        repo_a = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        repo_b = SampleItemRepository(session=db_session, tenant_id=tenant_b.id)

        await repo_a.create({"name": "A item 1"})
        await repo_a.create({"name": "A item 2"})
        await repo_b.create({"name": "B item 1"})

        assert await repo_a.count() == 2
        assert await repo_b.count() == 1

    async def test_delete_does_not_affect_other_tenant_data(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        repo_a = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        repo_b = SampleItemRepository(session=db_session, tenant_id=tenant_b.id)

        item_a = await repo_a.create({"name": "keep"})
        item_b = await repo_b.create({"name": "deletable"})

        # Tenant A tries to delete tenant B's item — must fail silently
        deleted = await repo_a.delete(item_b.id)
        assert deleted is False

        # B's item must still exist
        still_there = await repo_b.get(item_b.id)
        assert still_there is not None

        # A's item must be untouched
        a_item = await repo_a.get(item_a.id)
        assert a_item is not None

    async def test_two_tenants_same_data_structure_no_leakage(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        # Simulates realistic scenario: both tenants have items with similar names
        repo_a = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        repo_b = SampleItemRepository(session=db_session, tenant_id=tenant_b.id)

        for name in ["maintenance", "inspection", "repair"]:
            await repo_a.create({"name": name})
            await repo_b.create({"name": name})

        items_a = await repo_a.list()
        items_b = await repo_b.list()

        ids_a = {i.id for i in items_a}
        ids_b = {i.id for i in items_b}

        assert len(ids_a) == 3
        assert len(ids_b) == 3
        assert ids_a.isdisjoint(ids_b), "Tenant data must never overlap"
