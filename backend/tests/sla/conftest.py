from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.modules.catalog.models import Priority
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.sla.models import SlaPolicy
from app.modules.tenants.models import Tenant
from app.modules.users.models import Role, User, UserRole
from app.modules.hub.seed import seed_manutencao_for_tenant
from app.modules.users.seed import seed_default_roles_and_permissions


@pytest.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="SLA Test Corp", slug=f"sla-{uuid.uuid4().hex[:8]}")
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
async def default_priority(db_session: AsyncSession, seeded_tenant: Tenant) -> Priority:
    stmt = select(Priority).where(Priority.tenant_id == seeded_tenant.id, Priority.code == "low")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def high_priority(db_session: AsyncSession, seeded_tenant: Tenant) -> Priority:
    stmt = select(Priority).where(Priority.tenant_id == seeded_tenant.id, Priority.code == "high")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def sla_policy(
    db_session: AsyncSession, seeded_tenant: Tenant, default_priority: Priority
) -> SlaPolicy:
    policy = SlaPolicy(
        tenant_id=seeded_tenant.id,
        ticket_type="predial",
        priority_id=default_priority.id,
        team_id=None,
        attendance_minutes=60,
        resolution_minutes=480,
        alert_threshold_pct=80,
        is_active=True,
    )
    db_session.add(policy)
    await db_session.flush()
    return policy


@pytest.fixture
async def admin_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "admin")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def admin_user(db_session: AsyncSession, seeded_tenant: Tenant, admin_role: Role) -> User:
    user = User(
        tenant_id=seeded_tenant.id,
        name="Admin SLA",
        email=f"admin-sla-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("test1234"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=admin_role.id))
    await db_session.flush()
    return user


def _make_client(db_session: AsyncSession, auth_header: str | None = None) -> AsyncClient:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    headers = {"Authorization": auth_header} if auth_header else {}
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers)


@pytest.fixture
async def admin_client(db_session: AsyncSession, admin_user: User) -> AsyncClient:
    stmt = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == admin_user.id)
    )
    result = await db_session.execute(stmt)
    role_codes = list(result.scalars().all())
    token = create_access_token(str(admin_user.id), admin_user.tenant_id, role_codes)
    bearer = f"Bearer {token}"
    async with _make_client(db_session, auth_header=bearer) as client:
        yield client
    from app.main import app

    app.dependency_overrides.pop(get_db, None)
