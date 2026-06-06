from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant


class TestSystemAdminGuard:
    """Verifies that /admin/tenants endpoints are inaccessible to non-super-admins."""

    async def test_unauthenticated_get_returns_401(self, anon_client: AsyncClient):
        resp = await anon_client.get("/api/v1/admin/tenants")
        assert resp.status_code == 401

    async def test_regular_admin_get_returns_403(self, regular_admin_client: AsyncClient):
        resp = await regular_admin_client.get("/api/v1/admin/tenants")
        assert resp.status_code == 403

    async def test_regular_admin_post_returns_403(self, regular_admin_client: AsyncClient):
        resp = await regular_admin_client.post(
            "/api/v1/admin/tenants",
            json={
                "name": "X",
                "slug": f"x-{uuid.uuid4().hex[:6]}",
                "admin_name": "X",
                "admin_email": "x@x.com",
                "admin_password": "securepass123",
            },
        )
        assert resp.status_code == 403

    async def test_regular_admin_activate_returns_403(
        self, regular_admin_client: AsyncClient, db_session: AsyncSession
    ):
        tenant = Tenant(name="T", slug=f"t-{uuid.uuid4().hex[:6]}", is_active=False)
        db_session.add(tenant)
        await db_session.flush()

        resp = await regular_admin_client.post(
            f"/api/v1/admin/tenants/{tenant.id}/activate"
        )
        assert resp.status_code == 403

    async def test_super_admin_can_access_all_endpoints(
        self, super_admin_client: AsyncClient, base_tenant: Tenant
    ):
        resp = await super_admin_client.get("/api/v1/admin/tenants")
        assert resp.status_code == 200

        resp = await super_admin_client.get(f"/api/v1/admin/tenants/{base_tenant.id}")
        assert resp.status_code == 200
