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
from app.modules.teams.models import Team, TeamMember
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import Role, User, UserRole
from app.modules.hub.seed import seed_manutencao_for_tenant
from app.modules.users.seed import seed_default_roles_and_permissions


@pytest.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Dashboard Corp", slug=f"dash-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def seeded_tenant(db_session: AsyncSession, tenant: Tenant) -> Tenant:
    await seed_default_roles_and_permissions(db_session, tenant.id)
    await seed_catalog_defaults(db_session, tenant.id)
    await seed_manutencao_for_tenant(db_session, tenant.id)
    await db_session.flush()
    return tenant


@pytest.fixture
async def admin_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "admin")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def supervisor_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "supervisor")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def technician_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "technician")
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
    user = _make_user(seeded_tenant.id, "Admin", f"admin-{uuid.uuid4().hex[:6]}@test.com")
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=admin_role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def supervisor_user(
    db_session: AsyncSession, seeded_tenant: Tenant, supervisor_role: Role
) -> User:
    user = _make_user(seeded_tenant.id, "Supervisor", f"sup-{uuid.uuid4().hex[:6]}@test.com")
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=supervisor_role.id)
    )
    await db_session.flush()
    return user


@pytest.fixture
async def technician_user(
    db_session: AsyncSession, seeded_tenant: Tenant, technician_role: Role
) -> User:
    user = _make_user(seeded_tenant.id, "Técnico", f"tech-{uuid.uuid4().hex[:6]}@test.com")
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=technician_role.id)
    )
    await db_session.flush()
    return user


@pytest.fixture
async def default_priority(db_session: AsyncSession, seeded_tenant: Tenant) -> Priority:
    stmt = select(Priority).where(Priority.tenant_id == seeded_tenant.id, Priority.code == "low")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def status_new(db_session: AsyncSession, seeded_tenant: Tenant) -> Status:
    stmt = select(Status).where(Status.tenant_id == seeded_tenant.id, Status.code == "new")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def status_in_progress(db_session: AsyncSession, seeded_tenant: Tenant) -> Status:
    stmt = select(Status).where(
        Status.tenant_id == seeded_tenant.id, Status.code == "in_progress"
    )
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def team(db_session: AsyncSession, seeded_tenant: Tenant, supervisor_user: User) -> Team:
    t = Team(tenant_id=seeded_tenant.id, name="Equipe Teste", is_active=True)
    db_session.add(t)
    await db_session.flush()
    db_session.add(
        TeamMember(tenant_id=seeded_tenant.id, team_id=t.id, user_id=supervisor_user.id)
    )
    await db_session.flush()
    return t


@pytest.fixture
async def assigned_ticket(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    technician_user: User,
    admin_user: User,
    default_priority: Priority,
    status_new: Status,
    team: Team,
) -> Ticket:
    t = Ticket(
        tenant_id=seeded_tenant.id,
        type="predial",
        title="Ticket atribuído ao técnico",
        description="Descrição do ticket.",
        priority_id=default_priority.id,
        status_id=status_new.id,
        requester_id=admin_user.id,
        assignee_id=technician_user.id,
        team_id=team.id,
    )
    db_session.add(t)
    await db_session.flush()
    return t


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
async def admin_client(db_session: AsyncSession, admin_user: User) -> AsyncClient:
    bearer = await _make_bearer(admin_user, db_session)
    async with _make_client(db_session, auth_header=bearer) as client:
        yield client
    from app.main import app

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def supervisor_client(db_session: AsyncSession, supervisor_user: User) -> AsyncClient:
    bearer = await _make_bearer(supervisor_user, db_session)
    async with _make_client(db_session, auth_header=bearer) as client:
        yield client
    from app.main import app

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def tech_client(db_session: AsyncSession, technician_user: User) -> AsyncClient:
    bearer = await _make_bearer(technician_user, db_session)
    async with _make_client(db_session, auth_header=bearer) as client:
        yield client
    from app.main import app

    app.dependency_overrides.pop(get_db, None)
