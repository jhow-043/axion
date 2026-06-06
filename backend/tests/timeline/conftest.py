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
from app.modules.locations.models import Location
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import Role, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


@pytest.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Timeline Test Corp", slug=f"tl-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def seeded_tenant(db_session: AsyncSession, tenant: Tenant) -> Tenant:
    await seed_default_roles_and_permissions(db_session, tenant.id)
    await seed_catalog_defaults(db_session, tenant.id)
    await db_session.flush()
    return tenant


@pytest.fixture
async def admin_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "admin")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def requester_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "requester")
    result = await db_session.execute(stmt)
    return result.scalar_one()


def _make_user(tenant_id, name, email):
    return User(
        tenant_id=tenant_id,
        name=name,
        email=email,
        password_hash=hash_password("test1234"),
        is_active=True,
    )


@pytest.fixture
async def admin_user(db_session: AsyncSession, seeded_tenant: Tenant, admin_role: Role) -> User:
    user = _make_user(seeded_tenant.id, "Admin", f"admin-{uuid.uuid4().hex[:6]}@tl.test")
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=admin_role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def requester_user(
    db_session: AsyncSession, seeded_tenant: Tenant, requester_role: Role
) -> User:
    user = _make_user(seeded_tenant.id, "Requester", f"req-{uuid.uuid4().hex[:6]}@tl.test")
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=requester_role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def active_location(db_session: AsyncSession, seeded_tenant: Tenant) -> Location:
    loc = Location(tenant_id=seeded_tenant.id, name=f"Sala-{uuid.uuid4().hex[:4]}", is_active=True)
    db_session.add(loc)
    await db_session.flush()
    return loc


@pytest.fixture
async def default_priority(db_session: AsyncSession, seeded_tenant: Tenant) -> Priority:
    stmt = select(Priority).where(Priority.tenant_id == seeded_tenant.id, Priority.code == "low")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def default_status_new(db_session: AsyncSession, seeded_tenant: Tenant) -> Status:
    stmt = select(Status).where(Status.tenant_id == seeded_tenant.id, Status.code == "new")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def sample_ticket(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    requester_user: User,
    default_priority: Priority,
    default_status_new: Status,
    active_location: Location,
) -> Ticket:
    ticket = Ticket(
        tenant_id=seeded_tenant.id,
        type="predial",
        title="Ticket para timeline",
        description="Desc",
        priority_id=default_priority.id,
        status_id=default_status_new.id,
        location_id=active_location.id,
        requester_id=requester_user.id,
    )
    db_session.add(ticket)
    await db_session.flush()
    return ticket


async def _make_bearer(user: User, db_session: AsyncSession) -> str:
    stmt = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    result = await db_session.execute(stmt)
    role_codes = list(result.scalars().all())
    token = create_access_token(str(user.id), user.tenant_id, role_codes)
    return f"Bearer {token}"


def _make_client(db_session: AsyncSession, auth_header: str | None = None) -> AsyncClient:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    headers = {"Authorization": auth_header} if auth_header else {}
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers)


@pytest.fixture
async def admin_client(db_session: AsyncSession, admin_user: User):
    bearer = await _make_bearer(admin_user, db_session)
    async with _make_client(db_session, auth_header=bearer) as client:
        yield client
    from app.main import app

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def requester_client(db_session: AsyncSession, requester_user: User):
    bearer = await _make_bearer(requester_user, db_session)
    async with _make_client(db_session, auth_header=bearer) as client:
        yield client
    from app.main import app

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def anon_client(db_session: AsyncSession):
    async with _make_client(db_session) as client:
        yield client
    from app.main import app

    app.dependency_overrides.pop(get_db, None)
