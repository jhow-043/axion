from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import ALL_PERMISSIONS, SYSTEM_ADMIN
from app.core.security import create_access_token, hash_password
from app.modules.hub.models import Module
from app.modules.hub.seed import seed_manutencao_for_tenant, seed_module_manutencao
from app.modules.tenants.models import Tenant
from app.modules.users.models import Permission, Role, RolePermission, User, UserRole
from app.modules.users.seed import seed_default_roles_and_permissions


@pytest.fixture
async def tenant_a(db_session: AsyncSession):
    from app.modules.tenants.models import Tenant

    t = Tenant(name="Empresa A", slug="empresa-a")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def tenant_b(db_session: AsyncSession):
    from app.modules.tenants.models import Tenant

    t = Tenant(name="Empresa B", slug="empresa-b")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def manutencao_module(db_session: AsyncSession) -> Module:
    return await seed_module_manutencao(db_session)


@pytest.fixture
async def tenant_a_with_module(db_session: AsyncSession, tenant_a, manutencao_module: Module):
    await seed_manutencao_for_tenant(db_session, tenant_a.id)
    return tenant_a


@pytest.fixture
async def user_a(db_session: AsyncSession, tenant_a):
    role = Role(tenant_id=tenant_a.id, name="Admin", code="admin")
    db_session.add(role)
    await db_session.flush()

    user = User(
        tenant_id=tenant_a.id,
        name="Usuário A",
        email="user-a@empresa.com",
        password_hash=hash_password("senha123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(tenant_id=tenant_a.id, user_id=user.id, role_id=role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def user_b(db_session: AsyncSession, tenant_b):
    role = Role(tenant_id=tenant_b.id, name="Admin", code="admin")
    db_session.add(role)
    await db_session.flush()

    user = User(
        tenant_id=tenant_b.id,
        name="Usuário B",
        email="user-b@empresa.com",
        password_hash=hash_password("senha123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(tenant_id=tenant_b.id, user_id=user.id, role_id=role.id))
    await db_session.flush()
    return user


# ── P21: fixtures for platform module management endpoints ─────────────────────


async def _ensure_permissions(db: AsyncSession) -> dict[str, Permission]:
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
async def platform_tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Platform Corp", slug=f"platform-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    await seed_default_roles_and_permissions(db_session, t.id)
    await db_session.flush()
    return t


@pytest.fixture
async def target_tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Target Corp", slug=f"target-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def system_admin_user(db_session: AsyncSession, platform_tenant: Tenant) -> User:
    perm_map = await _ensure_permissions(db_session)

    role = Role(
        tenant_id=platform_tenant.id,
        name="Super Admin",
        code="system_admin_role",
    )
    db_session.add(role)
    await db_session.flush()

    db_session.add(RolePermission(role_id=role.id, permission_id=perm_map[SYSTEM_ADMIN].id))
    await db_session.flush()

    user = User(
        tenant_id=platform_tenant.id,
        name="Super Admin",
        email=f"superadmin-{uuid.uuid4().hex[:6]}@hub.test",
        password_hash=hash_password("superpass123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(UserRole(tenant_id=platform_tenant.id, user_id=user.id, role_id=role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def regular_platform_user(db_session: AsyncSession, platform_tenant: Tenant) -> User:
    stmt = select(Role).where(Role.tenant_id == platform_tenant.id, Role.code == "admin")
    result = await db_session.execute(stmt)
    admin_role = result.scalar_one()

    user = User(
        tenant_id=platform_tenant.id,
        name="Regular Admin",
        email=f"regular-{uuid.uuid4().hex[:6]}@hub.test",
        password_hash=hash_password("pass123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    db_session.add(
        UserRole(tenant_id=platform_tenant.id, user_id=user.id, role_id=admin_role.id)
    )
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
async def super_admin_client(db_session: AsyncSession, system_admin_user: User):
    token = await _make_token(system_admin_user, db_session)
    async with _make_client(db_session, token) as client:
        yield client
    from app.main import app
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def regular_platform_client(db_session: AsyncSession, regular_platform_user: User):
    token = await _make_token(regular_platform_user, db_session)
    async with _make_client(db_session, token) as client:
        yield client
    from app.main import app
    app.dependency_overrides.pop(get_db, None)
