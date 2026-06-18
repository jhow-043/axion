from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.security import hash_password
from app.modules.hub.seed import seed_manutencao_for_tenant, seed_module_manutencao
from app.modules.tenants.models import Tenant
from app.modules.users.models import Role, User, UserRole


async def _login(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
async def tenant_with_module(db_session: AsyncSession):
    t = Tenant(name="Com Módulo", slug="com-modulo")
    db_session.add(t)
    await db_session.flush()
    await seed_manutencao_for_tenant(db_session, t.id)
    return t


@pytest.fixture
async def tenant_without_module(db_session: AsyncSession):
    t = Tenant(name="Sem Módulo", slug="sem-modulo")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def user_with_module(db_session: AsyncSession, tenant_with_module):
    role = Role(tenant_id=tenant_with_module.id, name="Admin", code="admin")
    db_session.add(role)
    await db_session.flush()
    user = User(
        tenant_id=tenant_with_module.id,
        name="João Com",
        email="joao-com@empresa.com",
        password_hash=hash_password("senha123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=tenant_with_module.id, user_id=user.id, role_id=role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def user_without_module(db_session: AsyncSession, tenant_without_module):
    role = Role(tenant_id=tenant_without_module.id, name="Admin", code="admin")
    db_session.add(role)
    await db_session.flush()
    user = User(
        tenant_id=tenant_without_module.id,
        name="João Sem",
        email="joao-sem@empresa.com",
        password_hash=hash_password("senha123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRole(tenant_id=tenant_without_module.id, user_id=user.id, role_id=role.id))
    await db_session.flush()
    return user


@pytest.fixture
async def http_client(db_session: AsyncSession) -> AsyncClient:
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


class TestGetMeEnabledModules:
    async def test_get_me_returns_manutencao_when_module_enabled(
        self, http_client: AsyncClient, user_with_module: User
    ):
        token = await _login(http_client, "joao-com@empresa.com", "senha123")
        r = await http_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert "enabled_modules" in data
        assert "manutencao" in data["enabled_modules"]

    async def test_get_me_returns_empty_modules_when_none_enabled(
        self, http_client: AsyncClient, user_without_module: User
    ):
        token = await _login(http_client, "joao-sem@empresa.com", "senha123")
        r = await http_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert "enabled_modules" in data
        assert data["enabled_modules"] == []


class TestRequireModuleDependency:
    async def test_route_with_require_module_returns_200_when_enabled(
        self, http_client: AsyncClient, user_with_module: User, db_session: AsyncSession
    ):
        """Adds a temporary route to verify require_module gate."""
        from fastapi import APIRouter

        from app.core.deps import require_module
        from app.main import app

        test_router = APIRouter()

        @test_router.get("/test/module-gate")
        async def _gate(_=__import__("fastapi").Depends(require_module("manutencao"))):
            return {"ok": True}

        app.include_router(test_router, prefix="/api/v1")

        token = await _login(http_client, "joao-com@empresa.com", "senha123")
        r = await http_client.get(
            "/api/v1/test/module-gate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    async def test_route_with_require_module_returns_404_when_not_enabled(
        self, http_client: AsyncClient, user_without_module: User, db_session: AsyncSession
    ):
        token = await _login(http_client, "joao-sem@empresa.com", "senha123")
        r = await http_client.get(
            "/api/v1/test/module-gate",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 404


class TestProvisionTenantSeeding:
    async def test_provision_tenant_enables_manutencao_module(
        self, http_client: AsyncClient, db_session: AsyncSession
    ):
        from app.modules.hub.repository import ModuleRepository

        # Ensure the module catalogue entry exists first (normally done by migration seed)
        await seed_module_manutencao(db_session)

        # Provision a new tenant via the super-admin API
        # We need a system_admin user to do this
        platform_tenant = Tenant(name="Plataforma", slug="plataforma", is_system=True)
        db_session.add(platform_tenant)
        await db_session.flush()

        from app.modules.users.models import Permission, RolePermission

        admin_role = Role(tenant_id=platform_tenant.id, name="Super Admin", code="system_admin")
        db_session.add(admin_role)
        await db_session.flush()

        sys_perm = Permission(code="system_admin", name="System Admin")
        db_session.add(sys_perm)
        await db_session.flush()

        db_session.add(RolePermission(role_id=admin_role.id, permission_id=sys_perm.id))
        await db_session.flush()

        super_user = User(
            tenant_id=platform_tenant.id,
            name="Super Admin",
            email="super@plataforma.com",
            password_hash=hash_password("senha123"),
            is_active=True,
        )
        db_session.add(super_user)
        await db_session.flush()
        db_session.add(
            UserRole(tenant_id=platform_tenant.id, user_id=super_user.id, role_id=admin_role.id)
        )
        await db_session.flush()

        token = await _login(http_client, "super@plataforma.com", "senha123")

        r = await http_client.post(
            "/api/v1/admin/tenants",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Nova Empresa",
                "slug": "nova-empresa",
                "admin_name": "Admin Nova",
                "admin_email": "admin@nova.com",
                "admin_password": "senhaforte123",
            },
        )
        assert r.status_code == 201, r.text
        from uuid import UUID

        new_tenant_id = UUID(r.json()["id"])

        repo = ModuleRepository(db_session)
        assert await repo.is_enabled(new_tenant_id, "manutencao") is True
