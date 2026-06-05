"""Tenant isolation tests for P15 — Dashboards Operacionais.

Verifies that data from one tenant is never visible to another tenant's users."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.modules.catalog.models import Priority, Status
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import Role, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions

# ── Fixtures for two tenants ──────────────────────────────────────────────────


@pytest.fixture
async def tenant_a(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Empresa A", slug=f"empresa-a-{uuid.uuid4().hex[:6]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def tenant_b(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Empresa B", slug=f"empresa-b-{uuid.uuid4().hex[:6]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def seeded_a(db_session: AsyncSession, tenant_a: Tenant) -> Tenant:
    await seed_default_roles_and_permissions(db_session, tenant_a.id)
    await seed_catalog_defaults(db_session, tenant_a.id)
    await db_session.flush()
    return tenant_a


@pytest.fixture
async def seeded_b(db_session: AsyncSession, tenant_b: Tenant) -> Tenant:
    await seed_default_roles_and_permissions(db_session, tenant_b.id)
    await seed_catalog_defaults(db_session, tenant_b.id)
    await db_session.flush()
    return tenant_b


async def _make_tech(db: AsyncSession, tenant: Tenant) -> User:
    stmt = select(Role).where(Role.tenant_id == tenant.id, Role.code == "technician")
    result = await db.execute(stmt)
    role = result.scalar_one()
    user = User(
        tenant_id=tenant.id,
        name="Tech",
        email=f"tech-iso-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("test1234"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    db.add(UserRole(tenant_id=tenant.id, user_id=user.id, role_id=role.id))
    await db.flush()
    return user


async def _make_admin(db: AsyncSession, tenant: Tenant) -> User:
    stmt = select(Role).where(Role.tenant_id == tenant.id, Role.code == "admin")
    result = await db.execute(stmt)
    role = result.scalar_one()
    user = User(
        tenant_id=tenant.id,
        name="Admin",
        email=f"admin-iso-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("test1234"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    db.add(UserRole(tenant_id=tenant.id, user_id=user.id, role_id=role.id))
    await db.flush()
    return user


def _make_client(db: AsyncSession, token: str) -> AsyncClient:
    from app.main import app

    async def override():
        yield db

    app.dependency_overrides[get_db] = override
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )


def _token(user: User) -> str:
    return create_access_token(str(user.id), user.tenant_id, ["technician"])


def _admin_token(user: User) -> str:
    return create_access_token(str(user.id), user.tenant_id, ["admin"])


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_technician_dashboard_isolates_tenants(
    db_session: AsyncSession, seeded_a: Tenant, seeded_b: Tenant
):
    tech_a = await _make_tech(db_session, seeded_a)
    tech_b = await _make_tech(db_session, seeded_b)

    # Priority and status for each tenant
    stmt_a = select(Priority).where(Priority.tenant_id == seeded_a.id, Priority.code == "low")
    prio_a = (await db_session.execute(stmt_a)).scalar_one()
    stmt_sa = select(Status).where(Status.tenant_id == seeded_a.id, Status.code == "new")
    status_a = (await db_session.execute(stmt_sa)).scalar_one()

    # Create ticket in tenant B assigned to tech_b
    stmt_b = select(Priority).where(Priority.tenant_id == seeded_b.id, Priority.code == "low")
    prio_b = (await db_session.execute(stmt_b)).scalar_one()
    stmt_sb = select(Status).where(Status.tenant_id == seeded_b.id, Status.code == "new")
    status_b = (await db_session.execute(stmt_sb)).scalar_one()

    # Ticket for tech_a
    db_session.add(
        Ticket(
            tenant_id=seeded_a.id,
            type="predial",
            title="Ticket A",
            description="Desc",
            priority_id=prio_a.id,
            status_id=status_a.id,
            requester_id=tech_a.id,
            assignee_id=tech_a.id,
        )
    )
    # Ticket for tech_b — must NOT appear in tech_a's dashboard
    db_session.add(
        Ticket(
            tenant_id=seeded_b.id,
            type="predial",
            title="Ticket B",
            description="Desc",
            priority_id=prio_b.id,
            status_id=status_b.id,
            requester_id=tech_b.id,
            assignee_id=tech_b.id,
        )
    )
    await db_session.flush()

    token_a = _token(tech_a)
    async with _make_client(db_session, token_a) as client_a:
        resp = await client_a.get("/api/v1/dashboards/technician")

    from app.main import app

    app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    data = resp.json()
    # tech_a sees only their own ticket (1 total)
    assert data["assigned_tickets"]["total"] == 1


@pytest.mark.asyncio
async def test_supervisor_dashboard_isolates_tenants(
    db_session: AsyncSession, seeded_a: Tenant, seeded_b: Tenant
):
    admin_a = await _make_admin(db_session, seeded_a)
    admin_b = await _make_admin(db_session, seeded_b)

    stmt_a = select(Priority).where(Priority.tenant_id == seeded_a.id, Priority.code == "low")
    prio_a = (await db_session.execute(stmt_a)).scalar_one()
    stmt_sa = select(Status).where(Status.tenant_id == seeded_a.id, Status.code == "new")
    status_a = (await db_session.execute(stmt_sa)).scalar_one()

    stmt_b = select(Priority).where(Priority.tenant_id == seeded_b.id, Priority.code == "low")
    prio_b = (await db_session.execute(stmt_b)).scalar_one()
    stmt_sb = select(Status).where(Status.tenant_id == seeded_b.id, Status.code == "new")
    status_b = (await db_session.execute(stmt_sb)).scalar_one()

    for _ in range(2):
        db_session.add(
            Ticket(
                tenant_id=seeded_a.id,
                type="predial",
                title="Ticket Tenant A",
                description="Desc",
                priority_id=prio_a.id,
                status_id=status_a.id,
                requester_id=admin_a.id,
            )
        )
    for _ in range(5):
        db_session.add(
            Ticket(
                tenant_id=seeded_b.id,
                type="predial",
                title="Ticket Tenant B",
                description="Desc",
                priority_id=prio_b.id,
                status_id=status_b.id,
                requester_id=admin_b.id,
            )
        )
    await db_session.flush()

    token_a = _admin_token(admin_a)
    async with _make_client(db_session, token_a) as client_a:
        resp = await client_a.get("/api/v1/dashboards/supervisor")

    from app.main import app

    app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    data = resp.json()
    # Admin A sees only 2 tickets (their tenant's)
    assert data["summary"]["total_open"] == 2
