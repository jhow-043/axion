from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.modules.equipments.models import Equipment
from app.modules.locations.models import Sector
from app.modules.tenants.models import Tenant
from app.modules.users.models import Role, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


async def _create_tenant_with_admin(
    db_session: AsyncSession, slug_suffix: str
) -> tuple[Tenant, User, str]:
    tenant = Tenant(name=f"Tenant {slug_suffix}", slug=f"eq-iso-{slug_suffix}")
    db_session.add(tenant)
    await db_session.flush()

    await seed_default_roles_and_permissions(db_session, tenant.id)
    await db_session.flush()

    stmt = select(Role).where(Role.tenant_id == tenant.id, Role.code == "admin")
    result = await db_session.execute(stmt)
    role = result.scalar_one()

    user = User(
        tenant_id=tenant.id,
        name="Admin",
        email=f"admin-{slug_suffix}@iso.test",
        password_hash=hash_password("pass"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    ur = UserRole(tenant_id=tenant.id, user_id=user.id, role_id=role.id)
    db_session.add(ur)
    await db_session.flush()

    stmt2 = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    res2 = await db_session.execute(stmt2)
    role_codes = list(res2.scalars().all())
    token = create_access_token(str(user.id), tenant.id, role_codes)
    return tenant, user, f"Bearer {token}"


def _client(db_session: AsyncSession, token: str) -> AsyncClient:
    from app.main import app

    async def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": token},
    )


@pytest.fixture
async def two_tenants(db_session: AsyncSession):
    t1, u1, tok1 = await _create_tenant_with_admin(db_session, uuid.uuid4().hex[:6])
    t2, u2, tok2 = await _create_tenant_with_admin(db_session, uuid.uuid4().hex[:6])

    sector1 = Sector(tenant_id=t1.id, name="S1", is_active=True)
    sector2 = Sector(tenant_id=t2.id, name="S2", is_active=True)
    db_session.add_all([sector1, sector2])
    await db_session.flush()

    yield t1, t2, tok1, tok2, sector1, sector2, u1, u2

    from app.main import app

    app.dependency_overrides.pop(get_db, None)


class TestTenantIsolation:
    async def test_tenant_a_cannot_see_tenant_b_equipments(
        self, db_session: AsyncSession, two_tenants
    ):
        t1, t2, tok1, tok2, s1, s2, u1, u2 = two_tenants

        eq_b = Equipment(
            tenant_id=t2.id,
            code="EQ-B",
            name="Equipamento do Tenant B",
            sector_id=s2.id,
            created_by=u2.id,
        )
        db_session.add(eq_b)
        await db_session.flush()

        async with _client(db_session, tok1) as c:
            resp = await c.get("/api/v1/equipments")
            assert resp.status_code == 200
            ids = [i["id"] for i in resp.json()["items"]]
            assert str(eq_b.id) not in ids

    async def test_tenant_a_gets_404_for_tenant_b_equipment(
        self, db_session: AsyncSession, two_tenants
    ):
        t1, t2, tok1, tok2, s1, s2, u1, u2 = two_tenants

        eq_b = Equipment(
            tenant_id=t2.id,
            code="EQ-B2",
            name="Equipamento Isolado",
            sector_id=s2.id,
            created_by=u2.id,
        )
        db_session.add(eq_b)
        await db_session.flush()

        async with _client(db_session, tok1) as c:
            # INV-02: cross-tenant must return 404 not 403
            resp = await c.get(f"/api/v1/equipments/{eq_b.id}")
            assert resp.status_code == 404

    async def test_tenant_a_cannot_deactivate_tenant_b_equipment(
        self, db_session: AsyncSession, two_tenants
    ):
        t1, t2, tok1, tok2, s1, s2, u1, u2 = two_tenants

        eq_b = Equipment(
            tenant_id=t2.id,
            code="EQ-B3",
            name="Eq B deactivate",
            sector_id=s2.id,
            created_by=u2.id,
        )
        db_session.add(eq_b)
        await db_session.flush()

        async with _client(db_session, tok1) as c:
            resp = await c.post(f"/api/v1/equipments/{eq_b.id}/deactivate")
            assert resp.status_code == 404

    async def test_created_equipment_scoped_to_tenant(self, db_session: AsyncSession, two_tenants):
        t1, t2, tok1, tok2, s1, s2, u1, u2 = two_tenants

        async with _client(db_session, tok1) as c:
            resp = await c.post(
                "/api/v1/equipments",
                json={"code": "EQ-T1", "name": "Bomba T1", "sector_id": str(s1.id)},
            )
            assert resp.status_code == 201
            assert resp.json()["tenant_id"] == str(t1.id)

    async def test_tenant_a_cannot_use_tenant_b_sector(self, db_session: AsyncSession, two_tenants):
        t1, t2, tok1, tok2, s1, s2, u1, u2 = two_tenants

        async with _client(db_session, tok1) as c:
            # sector s2 belongs to t2 — must appear as "not found" to t1 (INV-02)
            resp = await c.post(
                "/api/v1/equipments",
                json={"code": "EQ-X", "name": "Cross", "sector_id": str(s2.id)},
            )
            assert resp.status_code == 404
