"""P24 — Integration tests verifying require_module("manutencao") returns 404
for tenants that do not have the module enabled.

Tests for tenants WITH the module are covered by the existing integration suites
in tests/tickets/, tests/dashboards/, etc. — this file only tests the gating path.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.tenants.models import Tenant
from app.modules.users.models import Role, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def tenant_no_module(db_session: AsyncSession) -> Tenant:
    """Tenant with roles seeded but NO module enabled."""
    t = Tenant(name="No-Module Corp", slug=f"nomod-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    await seed_default_roles_and_permissions(db_session, t.id)
    await seed_catalog_defaults(db_session, t.id)
    await db_session.flush()
    return t


@pytest.fixture
async def admin_user_no_module(
    db_session: AsyncSession, tenant_no_module: Tenant
) -> User:
    from sqlalchemy import select

    stmt = select(Role).where(
        Role.tenant_id == tenant_no_module.id, Role.code == "admin"
    )
    result = await db_session.execute(stmt)
    admin_role = result.scalar_one()

    user = User(
        tenant_id=tenant_no_module.id,
        name="Admin No Module",
        email=f"admin-nm-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("test1234"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserRole(
            tenant_id=tenant_no_module.id,
            user_id=user.id,
            role_id=admin_role.id,
        )
    )
    await db_session.flush()
    return user


@pytest.fixture
async def no_module_client(
    db_session: AsyncSession, admin_user_no_module: User
) -> AsyncClient:
    from app.main import app

    token = create_access_token(
        str(admin_user_no_module.id),
        admin_user_no_module.tenant_id,
        ["admin"],
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestModuleGating:
    async def test_tickets_list_returns_404_without_module(
        self, no_module_client: AsyncClient
    ):
        resp = await no_module_client.get("/api/v1/tickets")
        assert resp.status_code == 404

    async def test_tickets_create_returns_404_without_module(
        self, no_module_client: AsyncClient
    ):
        resp = await no_module_client.post("/api/v1/tickets", json={})
        assert resp.status_code == 404

    async def test_equipments_returns_404_without_module(
        self, no_module_client: AsyncClient
    ):
        resp = await no_module_client.get("/api/v1/equipments")
        assert resp.status_code == 404

    async def test_sla_returns_404_without_module(
        self, no_module_client: AsyncClient
    ):
        resp = await no_module_client.get("/api/v1/sla")
        assert resp.status_code == 404

    async def test_dashboards_management_returns_404_without_module(
        self, no_module_client: AsyncClient
    ):
        resp = await no_module_client.get("/api/v1/dashboards/management")
        assert resp.status_code == 404

    async def test_reports_returns_404_without_module(
        self, no_module_client: AsyncClient
    ):
        resp = await no_module_client.get("/api/v1/reports/tickets")
        assert resp.status_code == 404

    async def test_sectors_returns_404_without_module(
        self, no_module_client: AsyncClient
    ):
        resp = await no_module_client.get("/api/v1/sectors")
        assert resp.status_code == 404

    async def test_catalog_returns_404_without_module(
        self, no_module_client: AsyncClient
    ):
        resp = await no_module_client.get("/api/v1/catalog/priorities")
        assert resp.status_code == 404

    async def test_users_endpoint_accessible_without_module(
        self, no_module_client: AsyncClient
    ):
        """Platform endpoint — must NOT be gated by module."""
        resp = await no_module_client.get("/api/v1/users")
        assert resp.status_code != 404

    async def test_auth_me_accessible_without_module(
        self, no_module_client: AsyncClient
    ):
        """Core auth endpoint — must NOT be gated by module."""
        resp = await no_module_client.get("/api/v1/auth/me")
        assert resp.status_code in (200, 401)
