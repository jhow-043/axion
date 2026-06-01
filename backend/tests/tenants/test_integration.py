from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant
from app.shared.tenant_context import get_tenant, tenant_context
from tests.tenants._models import SampleItemRepository


class TestBaseRepositoryCreate:
    async def test_create_sets_tenant_id_automatically(
        self, db_session: AsyncSession, tenant_a: Tenant
    ):
        # CA: BaseRepository.create(data) sempre seta tenant_id sem precisar passá-lo
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        item = await repo.create({"name": "item alpha"})

        assert item.tenant_id == tenant_a.id
        assert item.id is not None

    async def test_create_overrides_caller_supplied_tenant_id(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        # INV-01: even if caller passes a different tenant_id, repository enforces own tenant
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        item = await repo.create({"name": "item", "tenant_id": tenant_b.id})

        assert item.tenant_id == tenant_a.id

    async def test_create_assigns_uuid_primary_key(
        self, db_session: AsyncSession, tenant_a: Tenant
    ):
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        item = await repo.create({"name": "named item"})

        assert isinstance(item.id, uuid.UUID)


class TestBaseRepositoryGet:
    async def test_get_returns_record_for_correct_tenant(
        self, db_session: AsyncSession, tenant_a: Tenant
    ):
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        created = await repo.create({"name": "findable"})

        found = await repo.get(created.id)

        assert found is not None
        assert found.id == created.id

    async def test_get_returns_none_for_cross_tenant_id(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        # CA: BaseRepository.get(id) nunca retorna registro de outro tenant (INV-02 → 404)
        repo_a = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        item = await repo_a.create({"name": "belongs to A"})

        repo_b = SampleItemRepository(session=db_session, tenant_id=tenant_b.id)
        result = await repo_b.get(item.id)

        assert result is None

    async def test_get_returns_none_for_nonexistent_id(
        self, db_session: AsyncSession, tenant_a: Tenant
    ):
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        result = await repo.get(uuid.uuid4())

        assert result is None


class TestBaseRepositoryList:
    async def test_list_returns_all_tenant_records(
        self, db_session: AsyncSession, tenant_a: Tenant
    ):
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        await repo.create({"name": "item 1"})
        await repo.create({"name": "item 2"})

        items = await repo.list()

        assert len(items) == 2

    async def test_list_respects_offset_and_limit(self, db_session: AsyncSession, tenant_a: Tenant):
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        for i in range(5):
            await repo.create({"name": f"item {i}"})

        page = await repo.list(offset=2, limit=2)

        assert len(page) == 2


class TestBaseRepositoryCount:
    async def test_count_returns_tenant_record_count(
        self, db_session: AsyncSession, tenant_a: Tenant
    ):
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        await repo.create({"name": "x"})
        await repo.create({"name": "y"})

        total = await repo.count()

        assert total == 2


class TestBaseRepositoryUpdate:
    async def test_update_modifies_existing_record(
        self, db_session: AsyncSession, tenant_a: Tenant
    ):
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        item = await repo.create({"name": "original"})

        updated = await repo.update(item.id, {"name": "modified"})

        assert updated is not None
        assert updated.name == "modified"

    async def test_update_returns_none_for_cross_tenant_id(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        repo_a = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        item = await repo_a.create({"name": "owned by A"})

        repo_b = SampleItemRepository(session=db_session, tenant_id=tenant_b.id)
        result = await repo_b.update(item.id, {"name": "hijacked"})

        assert result is None


class TestBaseRepositoryDelete:
    async def test_delete_removes_existing_record(self, db_session: AsyncSession, tenant_a: Tenant):
        repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        item = await repo.create({"name": "to delete"})

        deleted = await repo.delete(item.id)
        found = await repo.get(item.id)

        assert deleted is True
        assert found is None

    async def test_delete_returns_false_for_cross_tenant_id(
        self, db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
    ):
        repo_a = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
        item = await repo_a.create({"name": "owned by A"})

        repo_b = SampleItemRepository(session=db_session, tenant_id=tenant_b.id)
        result = await repo_b.delete(item.id)

        assert result is False


class TestCeleryTenantPattern:
    async def test_tenant_context_simulates_celery_worker(
        self, db_session: AsyncSession, tenant_a: Tenant
    ):
        # CA: Worker Celery com tenant_id no payload → contexto configurado corretamente
        assert get_tenant() is None

        with tenant_context(tenant_a.id):
            # Inside: ContextVar is set — worker can call get_current_tenant()
            assert get_tenant() == tenant_a.id
            repo = SampleItemRepository(session=db_session, tenant_id=tenant_a.id)
            item = await repo.create({"name": "celery item"})
            assert item.tenant_id == tenant_a.id

        # After: context restored — no tenant leakage between tasks
        assert get_tenant() is None

    async def test_tenant_context_resets_correctly_on_worker_error(
        self, db_session: AsyncSession, tenant_a: Tenant
    ):
        with pytest.raises(RuntimeError):
            with tenant_context(tenant_a.id):
                raise RuntimeError("worker failed")

        assert get_tenant() is None
