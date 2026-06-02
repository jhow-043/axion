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
    tenant = Tenant(name=f"Tenant {slug_suffix}", slug=f"loc-tenant-{slug_suffix}")
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
    from app.main import app

    suffix_a = uuid.uuid4().hex[:6]
    suffix_b = uuid.uuid4().hex[:6]

    _, user_a = await _make_tenant_with_admin(
        db_session,
        slug_suffix=suffix_a,
        admin_email=f"admin-{suffix_a}@a.com",
    )
    _, user_b = await _make_tenant_with_admin(
        db_session,
        slug_suffix=suffix_b,
        admin_email=f"admin-{suffix_b}@b.com",
    )

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ca:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cb:
            await _set_bearer(ca, user_a, db_session)
            await _set_bearer(cb, user_b, db_session)
            yield ca, cb

    app.dependency_overrides.pop(get_db, None)


class TestSectorTenantIsolation:
    async def test_list_returns_only_own_tenant_sectors(self, two_tenant_clients):
        ca, cb = two_tenant_clients
        await ca.post("/api/v1/sectors", json={"name": "Setor A"})
        await cb.post("/api/v1/sectors", json={"name": "Setor B"})

        resp_a = await ca.get("/api/v1/sectors")
        names_a = {s["name"] for s in resp_a.json()["items"]}
        resp_b = await cb.get("/api/v1/sectors")
        names_b = {s["name"] for s in resp_b.json()["items"]}

        assert "Setor A" in names_a
        assert "Setor B" not in names_a
        assert "Setor B" in names_b
        assert "Setor A" not in names_b

    async def test_get_cross_tenant_sector_returns_404(self, two_tenant_clients):
        """ADR-0002: cross-tenant access returns 404, never 403."""
        ca, cb = two_tenant_clients
        cr = await ca.post("/api/v1/sectors", json={"name": "Only For A"})
        sector_id = cr.json()["id"]
        resp = await cb.get(f"/api/v1/sectors/{sector_id}")
        assert resp.status_code == 404

    async def test_update_cross_tenant_sector_returns_404(self, two_tenant_clients):
        ca, cb = two_tenant_clients
        cr = await ca.post("/api/v1/sectors", json={"name": "Setor Privado"})
        sector_id = cr.json()["id"]
        resp = await cb.patch(f"/api/v1/sectors/{sector_id}", json={"name": "Hijacked"})
        assert resp.status_code == 404

    async def test_same_name_allowed_in_different_tenants(self, two_tenant_clients):
        ca, cb = two_tenant_clients
        resp_a = await ca.post("/api/v1/sectors", json={"name": "Shared Name"})
        assert resp_a.status_code == 201
        resp_b = await cb.post("/api/v1/sectors", json={"name": "Shared Name"})
        assert resp_b.status_code == 201


class TestLocationTenantIsolation:
    async def test_list_returns_only_own_tenant_locations(self, two_tenant_clients):
        ca, cb = two_tenant_clients
        await ca.post("/api/v1/locations", json={"name": "Local A"})
        await cb.post("/api/v1/locations", json={"name": "Local B"})

        resp_a = await ca.get("/api/v1/locations")
        names_a = {loc["name"] for loc in resp_a.json()["items"]}
        resp_b = await cb.get("/api/v1/locations")
        names_b = {loc["name"] for loc in resp_b.json()["items"]}

        assert "Local A" in names_a
        assert "Local B" not in names_a
        assert "Local B" in names_b
        assert "Local A" not in names_b

    async def test_get_cross_tenant_location_returns_404(self, two_tenant_clients):
        """ADR-0002: cross-tenant access returns 404, never 403."""
        ca, cb = two_tenant_clients
        cr = await ca.post("/api/v1/locations", json={"name": "Sala Secreta"})
        loc_id = cr.json()["id"]
        resp = await cb.get(f"/api/v1/locations/{loc_id}")
        assert resp.status_code == 404

    async def test_same_name_allowed_in_different_tenants(self, two_tenant_clients):
        ca, cb = two_tenant_clients
        resp_a = await ca.post("/api/v1/locations", json={"name": "Galpão Compartilhado"})
        assert resp_a.status_code == 201
        resp_b = await cb.post("/api/v1/locations", json={"name": "Galpão Compartilhado"})
        assert resp_b.status_code == 201
