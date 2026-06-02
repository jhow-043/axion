from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.modules.tenants.models import Tenant
from app.modules.users.models import Role, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


async def _make_tenant_with_admin(
    db_session: AsyncSession,
    *,
    slug_suffix: str,
    admin_email: str,
) -> tuple[Tenant, User]:
    tenant = Tenant(name=f"Tenant {slug_suffix}", slug=f"tenant-{slug_suffix}")
    db_session.add(tenant)
    await db_session.flush()

    await seed_default_roles_and_permissions(db_session, tenant.id)
    await db_session.flush()

    stmt = select(Role).where(Role.tenant_id == tenant.id, Role.code == "admin")
    result = await db_session.execute(stmt)
    admin_role = result.scalar_one()

    user = User(
        tenant_id=tenant.id,
        name=f"Admin {slug_suffix}",
        email=admin_email,
        password_hash=hash_password("pass1234"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    ur = UserRole(tenant_id=tenant.id, user_id=user.id, role_id=admin_role.id)
    db_session.add(ur)
    await db_session.flush()

    return tenant, user


async def _set_bearer(client: AsyncClient, user: User, db_session: AsyncSession) -> None:
    stmt = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    result = await db_session.execute(stmt)
    role_codes = list(result.scalars().all())
    token = create_access_token(str(user.id), user.tenant_id, role_codes)
    client.headers["Authorization"] = f"Bearer {token}"


@pytest.fixture
async def two_tenant_clients(db_session: AsyncSession):
    """Creates two isolated tenants with admin users.
    Returns (client_a, user_a, client_b, user_b)."""
    from app.main import app

    suffix_a = uuid.uuid4().hex[:6]
    suffix_b = uuid.uuid4().hex[:6]

    tenant_a, user_a = await _make_tenant_with_admin(
        db_session,
        slug_suffix=suffix_a,
        admin_email=f"admin-{suffix_a}@a.com",
    )
    tenant_b, user_b = await _make_tenant_with_admin(
        db_session,
        slug_suffix=suffix_b,
        admin_email=f"admin-{suffix_b}@b.com",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_a:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client_b:
            await _set_bearer(client_a, user_a, db_session)
            await _set_bearer(client_b, user_b, db_session)
            yield client_a, user_a, client_b, user_b

    app.dependency_overrides.pop(get_db, None)


class TestTenantIsolation:
    async def test_list_returns_only_own_tenant_users(self, two_tenant_clients):
        client_a, user_a, client_b, user_b = two_tenant_clients

        resp_a = await client_a.get("/api/v1/users")
        assert resp_a.status_code == 200
        ids_a = {u["id"] for u in resp_a.json()["items"]}

        resp_b = await client_b.get("/api/v1/users")
        assert resp_b.status_code == 200
        ids_b = {u["id"] for u in resp_b.json()["items"]}

        assert str(user_a.id) in ids_a
        assert str(user_b.id) not in ids_a

        assert str(user_b.id) in ids_b
        assert str(user_a.id) not in ids_b

    async def test_get_cross_tenant_user_returns_404_not_403(self, two_tenant_clients):
        """ADR-0002: cross-tenant access must return 404, never 403."""
        client_a, user_a, client_b, user_b = two_tenant_clients

        resp = await client_a.get(f"/api/v1/users/{user_b.id}")
        assert resp.status_code == 404

        resp = await client_b.get(f"/api/v1/users/{user_a.id}")
        assert resp.status_code == 404

    async def test_update_cross_tenant_user_returns_404(self, two_tenant_clients):
        client_a, user_a, client_b, user_b = two_tenant_clients

        resp = await client_a.patch(f"/api/v1/users/{user_b.id}", json={"name": "Hijacked"})
        assert resp.status_code == 404

    async def test_deactivate_cross_tenant_user_returns_404(self, two_tenant_clients):
        client_a, user_a, client_b, user_b = two_tenant_clients

        resp = await client_a.post(f"/api/v1/users/{user_b.id}/deactivate")
        assert resp.status_code == 404

    async def test_list_roles_returns_only_own_tenant_roles(self, two_tenant_clients):
        """Each tenant has its own copy of the default roles."""
        client_a, user_a, client_b, user_b = two_tenant_clients

        resp_a = await client_a.get("/api/v1/roles")
        assert resp_a.status_code == 200
        ids_a = {r["id"] for r in resp_a.json()}

        resp_b = await client_b.get("/api/v1/roles")
        assert resp_b.status_code == 200
        ids_b = {r["id"] for r in resp_b.json()}

        assert ids_a.isdisjoint(ids_b)
