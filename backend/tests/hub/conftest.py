from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.hub.models import Module
from app.modules.hub.seed import seed_manutencao_for_tenant, seed_module_manutencao
from app.modules.users.models import Role, User, UserRole


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
