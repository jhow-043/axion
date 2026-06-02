from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import hash_password

# Import models so Base.metadata picks them up in the session-scoped engine fixture.
from app.modules.auth.models import RefreshToken  # noqa: F401, F811
from app.modules.users.models import (  # noqa: F401, F811
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)


@pytest.fixture
async def tenant(db_session: AsyncSession):
    from app.modules.tenants.models import Tenant

    t = Tenant(name="Auth Test Corp", slug="auth-test-corp")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def technician_role(db_session: AsyncSession, tenant):
    role = Role(tenant_id=tenant.id, name="Técnico", code="technician")
    db_session.add(role)
    await db_session.flush()
    return role


@pytest.fixture
async def active_user(db_session: AsyncSession, tenant, technician_role):
    user = User(
        tenant_id=tenant.id,
        name="João Silva",
        email="joao@empresa.com",
        password_hash=hash_password("senha123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    user_role = UserRole(
        tenant_id=tenant.id,
        user_id=user.id,
        role_id=technician_role.id,
    )
    db_session.add(user_role)
    await db_session.flush()
    return user


@pytest.fixture
async def inactive_user(db_session: AsyncSession, tenant, technician_role):
    user = User(
        tenant_id=tenant.id,
        name="Inativo",
        email="inativo@empresa.com",
        password_hash=hash_password("senha123"),
        is_active=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def auth_client(db_session: AsyncSession) -> AsyncClient:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def authed_client(auth_client: AsyncClient, active_user: User, db_session: AsyncSession):
    """Client with a valid Bearer token already set."""
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": "joao@empresa.com", "password": "senha123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    auth_client.headers["Authorization"] = f"Bearer {token}"
    return auth_client
