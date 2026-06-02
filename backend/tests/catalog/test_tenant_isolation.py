from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.tenants.models import Tenant
from app.modules.users.models import Role, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


async def _make_tenant_with_admin(
    db_session: AsyncSession,
    *,
    slug_suffix: str,
    admin_email: str,
) -> tuple[Tenant, User]:
    tenant = Tenant(name=f"Catalog Tenant {slug_suffix}", slug=f"cat-tenant-{slug_suffix}")
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

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ca:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cb:
            await _set_bearer(ca, user_a, db_session)
            await _set_bearer(cb, user_b, db_session)
            yield ca, cb, tenant_a, tenant_b, db_session

    app.dependency_overrides.pop(get_db, None)


class TestCategoryTenantIsolation:
    async def test_list_returns_only_own_tenant_categories(self, two_tenant_clients):
        ca, cb, *_ = two_tenant_clients
        await ca.post("/api/v1/catalog/categories", json={"name": "Cat Tenant A"})
        await cb.post("/api/v1/catalog/categories", json={"name": "Cat Tenant B"})

        resp_a = await ca.get("/api/v1/catalog/categories")
        names_a = {c["name"] for c in resp_a.json()["items"]}
        resp_b = await cb.get("/api/v1/catalog/categories")
        names_b = {c["name"] for c in resp_b.json()["items"]}

        assert "Cat Tenant A" in names_a
        assert "Cat Tenant B" not in names_a
        assert "Cat Tenant B" in names_b
        assert "Cat Tenant A" not in names_b

    async def test_update_cross_tenant_category_returns_404(self, two_tenant_clients):
        """ADR-0002: cross-tenant access returns 404, never 403."""
        ca, cb, *_ = two_tenant_clients
        cr = await ca.post("/api/v1/catalog/categories", json={"name": "Privada de A"})
        cid = cr.json()["id"]
        resp = await cb.patch(f"/api/v1/catalog/categories/{cid}", json={"name": "Hijacked"})
        assert resp.status_code == 404

    async def test_same_category_name_allowed_in_different_tenants(self, two_tenant_clients):
        ca, cb, *_ = two_tenant_clients
        resp_a = await ca.post("/api/v1/catalog/categories", json={"name": "Mesma Cat"})
        assert resp_a.status_code == 201
        resp_b = await cb.post("/api/v1/catalog/categories", json={"name": "Mesma Cat"})
        assert resp_b.status_code == 201

    async def test_deactivate_cross_tenant_category_returns_404(self, two_tenant_clients):
        ca, cb, *_ = two_tenant_clients
        cr = await ca.post("/api/v1/catalog/categories", json={"name": "Só de A"})
        cid = cr.json()["id"]
        resp = await cb.post(f"/api/v1/catalog/categories/{cid}/deactivate")
        assert resp.status_code == 404


class TestPriorityTenantIsolation:
    async def test_list_returns_only_own_tenant_priorities(self, two_tenant_clients):
        ca, cb, tenant_a, tenant_b, db_session = two_tenant_clients
        await seed_catalog_defaults(db_session, tenant_a.id)
        await seed_catalog_defaults(db_session, tenant_b.id)

        resp_a = await ca.get("/api/v1/catalog/priorities")
        resp_b = await cb.get("/api/v1/catalog/priorities")

        ids_a = {p["id"] for p in resp_a.json()["items"]}
        ids_b = {p["id"] for p in resp_b.json()["items"]}

        assert ids_a.isdisjoint(ids_b), "tenants must not share priority records"

    async def test_update_cross_tenant_priority_returns_404(self, two_tenant_clients):
        """ADR-0002: cross-tenant access returns 404, never 403."""
        ca, cb, *_ = two_tenant_clients
        cr = await ca.post(
            "/api/v1/catalog/priorities", json={"name": "Alta de A", "code": "high_a", "order": 1}
        )
        pid = cr.json()["id"]
        resp = await cb.patch(f"/api/v1/catalog/priorities/{pid}", json={"name": "Hijacked"})
        assert resp.status_code == 404


class TestPendingReasonTenantIsolation:
    async def test_list_returns_only_own_tenant_reasons(self, two_tenant_clients):
        ca, cb, *_ = two_tenant_clients
        await ca.post("/api/v1/catalog/pending-reasons", json={"name": "Motivo de A"})
        await cb.post("/api/v1/catalog/pending-reasons", json={"name": "Motivo de B"})

        resp_a = await ca.get("/api/v1/catalog/pending-reasons")
        names_a = {r["name"] for r in resp_a.json()["items"]}
        resp_b = await cb.get("/api/v1/catalog/pending-reasons")
        names_b = {r["name"] for r in resp_b.json()["items"]}

        assert "Motivo de A" in names_a
        assert "Motivo de B" not in names_a

    async def test_deactivate_cross_tenant_reason_returns_404(self, two_tenant_clients):
        """ADR-0002: cross-tenant access returns 404, never 403."""
        ca, cb, *_ = two_tenant_clients
        cr = await ca.post("/api/v1/catalog/pending-reasons", json={"name": "Só de A"})
        rid = cr.json()["id"]
        resp = await cb.post(f"/api/v1/catalog/pending-reasons/{rid}/deactivate")
        assert resp.status_code == 404
