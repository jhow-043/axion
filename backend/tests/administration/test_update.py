from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.administration.repository import TenantRepository
from app.modules.administration.schemas import TenantCreate, TenantUpdate
from app.modules.administration.service import AdminService
from app.modules.tenants.models import Tenant


class TestUpdateTenant:
    async def test_update_name(self, db_session: AsyncSession):
        tenant = Tenant(name="Old Name", slug=f"old-{uuid.uuid4().hex[:6]}")
        db_session.add(tenant)
        await db_session.flush()

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)

        result = await svc.update_tenant(tenant.id, TenantUpdate(name="New Name"))
        assert result.name == "New Name"
        assert result.slug == tenant.slug

    async def test_update_slug_conflict_raises(self, db_session: AsyncSession):
        from app.core.exceptions import ConflictError

        t1 = Tenant(name="Corp A", slug=f"corp-a-{uuid.uuid4().hex[:6]}")
        t2 = Tenant(name="Corp B", slug=f"corp-b-{uuid.uuid4().hex[:6]}")
        db_session.add_all([t1, t2])
        await db_session.flush()

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)

        with pytest.raises(ConflictError):
            await svc.update_tenant(t2.id, TenantUpdate(slug=t1.slug))

    async def test_update_no_changes_returns_unchanged(self, db_session: AsyncSession):
        tenant = Tenant(name="Same", slug=f"same-{uuid.uuid4().hex[:6]}")
        db_session.add(tenant)
        await db_session.flush()

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)

        result = await svc.update_tenant(tenant.id, TenantUpdate())
        assert result.name == "Same"

    async def test_update_nonexistent_raises_not_found(self, db_session: AsyncSession):
        from app.core.exceptions import NotFoundError

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)

        with pytest.raises(NotFoundError):
            await svc.update_tenant(uuid.uuid4(), TenantUpdate(name="X"))

    async def test_patch_via_http(
        self, super_admin_client: AsyncClient, db_session: AsyncSession
    ):
        tenant = Tenant(name="Patch Me", slug=f"patch-{uuid.uuid4().hex[:6]}")
        db_session.add(tenant)
        await db_session.flush()

        resp = await super_admin_client.patch(
            f"/api/v1/admin/tenants/{tenant.id}",
            json={"name": "Patched Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Patched Name"


class TestSchemaValidation:
    def test_invalid_slug_raises(self):
        with pytest.raises(Exception):
            TenantCreate(
                name="X",
                slug="Invalid Slug!",
                admin_name="A",
                admin_email="a@b.com",
                admin_password="securepass123",
            )

    def test_short_password_raises(self):
        with pytest.raises(Exception):
            TenantCreate(
                name="X",
                slug="valid-slug",
                admin_name="A",
                admin_email="a@b.com",
                admin_password="short",
            )

    def test_update_invalid_slug_raises(self):
        with pytest.raises(Exception):
            TenantUpdate(slug="Invalid Slug!")

    def test_valid_create(self):
        data = TenantCreate(
            name="Corp",
            slug="corp-name",
            admin_name="Admin",
            admin_email="admin@corp.com",
            admin_password="securepass123",
        )
        assert data.slug == "corp-name"
