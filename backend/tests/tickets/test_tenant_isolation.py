"""Tenant isolation tests — ticket from tenant A is invisible to tenant B."""

from __future__ import annotations

import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.hub.seed import seed_manutencao_for_tenant
from app.modules.locations.models import Location
from app.modules.tenants.models import Tenant
from app.modules.users.models import Role, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


async def _setup_tenant(db_session: AsyncSession, slug: str) -> tuple[Tenant, User, str, Location]:
    tenant = Tenant(name=f"Corp {slug}", slug=slug)
    db_session.add(tenant)
    await db_session.flush()
    await seed_default_roles_and_permissions(db_session, tenant.id)
    await seed_catalog_defaults(db_session, tenant.id)
    await seed_manutencao_for_tenant(db_session, tenant.id)

    stmt = select(Role).where(Role.tenant_id == tenant.id, Role.code == "admin")
    result = await db_session.execute(stmt)
    role = result.scalar_one()

    user = User(
        tenant_id=tenant.id,
        name="Admin",
        email=f"admin-{slug}@test.com",
        password_hash=hash_password("pw"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=tenant.id, user_id=user.id, role_id=role.id))

    location = Location(
        tenant_id=tenant.id,
        name=f"Sala {slug}",
        is_active=True,
    )
    db_session.add(location)
    await db_session.flush()

    token = create_access_token(str(user.id), tenant.id, ["admin"])
    bearer = f"Bearer {token}"
    return tenant, user, bearer, location


def _make_client(db_session: AsyncSession, bearer: str) -> AsyncClient:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": bearer},
    )


class TestTicketTenantIsolation:
    async def test_ticket_from_tenant_a_invisible_to_tenant_b(self, db_session: AsyncSession):
        slug_a = f"iso-a-{uuid.uuid4().hex[:6]}"
        slug_b = f"iso-b-{uuid.uuid4().hex[:6]}"
        _, _, bearer_a, loc_a = await _setup_tenant(db_session, slug_a)
        _, _, bearer_b, _ = await _setup_tenant(db_session, slug_b)

        async with _make_client(db_session, bearer_a) as client_a:
            from app.modules.catalog.models import Priority

            prio_stmt = select(Priority).where(Priority.code == "low")
            prio_result = await db_session.execute(prio_stmt)
            # get first priority matching tenant A
            prios = prio_result.scalars().all()
            prio_a = next((p for p in prios if p.tenant_id == loc_a.tenant_id), None)
            assert prio_a is not None

            cr = await client_a.post(
                "/api/v1/tickets",
                json={
                    "type": "predial",
                    "title": "Tenant A ticket",
                    "description": "...",
                    "priority_id": str(prio_a.id),
                    "location_id": str(loc_a.id),
                },
            )
            assert cr.status_code == 201
            ticket_id = cr.json()["id"]

        async with _make_client(db_session, bearer_b) as client_b:
            resp = await client_b.get(f"/api/v1/tickets/{ticket_id}")
            assert resp.status_code == 404

        from app.main import app

        app.dependency_overrides.pop(get_db, None)

    async def test_ticket_list_scoped_to_tenant(self, db_session: AsyncSession):
        slug_a = f"list-a-{uuid.uuid4().hex[:6]}"
        slug_b = f"list-b-{uuid.uuid4().hex[:6]}"
        _, _, bearer_a, loc_a = await _setup_tenant(db_session, slug_a)
        _, _, bearer_b, _ = await _setup_tenant(db_session, slug_b)

        from app.modules.catalog.models import Priority

        async with _make_client(db_session, bearer_a) as client_a:
            prio_stmt = select(Priority).where(
                Priority.code == "low", Priority.tenant_id == loc_a.tenant_id
            )
            prio_result = await db_session.execute(prio_stmt)
            prio_a = prio_result.scalar_one()

            await client_a.post(
                "/api/v1/tickets",
                json={
                    "type": "predial",
                    "title": "Ticket A",
                    "description": "...",
                    "priority_id": str(prio_a.id),
                    "location_id": str(loc_a.id),
                },
            )

        async with _make_client(db_session, bearer_b) as client_b:
            resp = await client_b.get("/api/v1/tickets")
            assert resp.status_code == 200
            assert resp.json()["total"] == 0

        from app.main import app

        app.dependency_overrides.pop(get_db, None)
