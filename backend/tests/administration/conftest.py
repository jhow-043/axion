from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import ALL_PERMISSIONS, SYSTEM_ADMIN
from app.core.security import create_access_token, hash_password
from app.modules.tenants.models import Tenant
from app.modules.users.models import Permission, Role, RolePermission, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


@pytest.fixture
async def base_tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Admin Test Corp", slug=f"admin-test-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def seeded_tenant(db_session: AsyncSession, base_tenant: Tenant) -> Tenant:
    await seed_default_roles_and_permissions(db_session, base_tenant.id)
    await db_session.flush()
    return base_tenant


async def _ensure_permissions(db: AsyncSession) -> dict[str, Permission]:
    """Ensures all permissions exist and returns a code→Permission map."""
    existing_stmt = select(Permission)
    result = await db.execute(existing_stmt)
    existing = {p.code: p for p in result.scalars().all()}
    for code, name in ALL_PERMISSIONS:
        if code not in existing:
            perm = Permission(code=code, name=name)
            db.add(perm)
            await db.flush()
            existing[code] = perm
    return existing


@pytest.fixture
async def system_admin_user(db_session: AsyncSession, seeded_tenant: Tenant) -> User:
    """Creates a user with system_admin permission."""
    perm_map = await _ensure_permissions(db_session)

    # Create a super-admin role for the tenant
    role = Role(
        tenant_id=seeded_tenant.id,
        name="Super Admin",
        code="system_admin",
    )
    db_session.add(role)
    await db_session.flush()

    # Assign system_admin permission to this role
    system_perm = perm_map[SYSTEM_ADMIN]
    db_session.add(RolePermission(role_id=role.id, permission_id=system_perm.id))
    await db_session.flush()

    # Create user
    user = User(
        tenant_id=seeded_tenant.id,
        name="Super Admin User",
        email=f"superadmin-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("superpass123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Assign role
    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=role.id))
    await db_session.flush()

    return user


@pytest.fixture
async def regular_admin_user(db_session: AsyncSession, seeded_tenant: Tenant) -> User:
    """Creates a regular admin user (no system_admin permission)."""
    stmt = select(Role).where(Role.tenant_id == seeded_tenant.id, Role.code == "admin")
    result = await db_session.execute(stmt)
    admin_role = result.scalar_one()

    user = User(
        tenant_id=seeded_tenant.id,
        name="Regular Admin",
        email=f"admin-{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("adminpass123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(tenant_id=seeded_tenant.id, user_id=user.id, role_id=admin_role.id))
    await db_session.flush()

    return user


async def _make_token(user: User, db_session: AsyncSession) -> str:
    stmt = (
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id)
    )
    result = await db_session.execute(stmt)
    role_codes = list(result.scalars().all())
    return create_access_token(str(user.id), user.tenant_id, role_codes)


def _make_client(db_session: AsyncSession, token: str | None = None) -> AsyncClient:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers)


@pytest.fixture
async def anon_client(db_session: AsyncSession):
    async with _make_client(db_session) as client:
        yield client
    from app.main import app
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def super_admin_client(db_session: AsyncSession, system_admin_user: User):
    token = await _make_token(system_admin_user, db_session)
    async with _make_client(db_session, token) as client:
        yield client
    from app.main import app
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def regular_admin_client(db_session: AsyncSession, regular_admin_user: User):
    token = await _make_token(regular_admin_user, db_session)
    async with _make_client(db_session, token) as client:
        yield client
    from app.main import app
    app.dependency_overrides.pop(get_db, None)
