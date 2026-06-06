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


@pytest.fixture
async def tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Audit Test Corp", slug=f"audit-{uuid.uuid4().hex[:8]}")
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
async def technician_role(db_session: AsyncSession, seeded_tenant: Tenant) -> Role:
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "technician")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def admin_user(db_session: AsyncSession, seeded_tenant: Tenant, admin_role: Role) -> User:
    user = User(
        tenant_id=seeded_tenant.id,
        name="Admin Audit",
        email=f"admin-audit-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("test1234"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=admin_role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def technician_user(
    db_session: AsyncSession, seeded_tenant: Tenant, technician_role: Role
) -> User:
    user = User(
        tenant_id=seeded_tenant.id,
        name="Tech Audit",
        email=f"tech-audit-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("test1234"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=technician_role.id)
    )
    await db_session.flush()
    return user


def _make_client(db_session: AsyncSession, auth_header: str | None = None) -> AsyncClient:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    headers = {"Authorization": auth_header} if auth_header else {}
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers)


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


@pytest.fixture
async def admin_client(db_session: AsyncSession, admin_user: User) -> AsyncClient:
    bearer = await _make_bearer(admin_user, db_session)
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
