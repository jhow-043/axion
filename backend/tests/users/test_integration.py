from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant
from app.modules.users.models import User


class TestCreateUser:
    async def test_admin_creates_user_returns_201(
        self, admin_client: AsyncClient, seeded_tenant: Tenant
    ):
        resp = await admin_client.post(
            "/api/v1/users",
            json={"name": "New User", "email": "new@test.com", "password": "password123"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@test.com"
        assert data["is_active"] is True
        assert data["tenant_id"] == str(seeded_tenant.id)

    async def test_technician_cannot_create_user_returns_403(self, tech_client: AsyncClient):
        resp = await tech_client.post(
            "/api/v1/users",
            json={"name": "Blocked", "email": "blocked@test.com", "password": "password123"},
        )
        assert resp.status_code == 403

    async def test_duplicate_email_returns_409(self, admin_client: AsyncClient, admin_user: User):
        resp = await admin_client.post(
            "/api/v1/users",
            json={"name": "Dup", "email": "admin@test.com", "password": "password123"},
        )
        assert resp.status_code == 409

    async def test_unauthenticated_returns_401(self, users_client: AsyncClient):
        resp = await users_client.post(
            "/api/v1/users",
            json={"name": "X", "email": "x@test.com", "password": "password123"},
        )
        assert resp.status_code == 401


class TestListUsers:
    async def test_admin_lists_only_own_tenant_users(
        self, admin_client: AsyncClient, admin_user: User, technician_user: User
    ):
        resp = await admin_client.get("/api/v1/users")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        ids = [u["id"] for u in data["items"]]
        assert str(admin_user.id) in ids
        assert str(technician_user.id) in ids

    async def test_pagination_params_respected(self, admin_client: AsyncClient, admin_user: User):
        resp = await admin_client.get("/api/v1/users?page=1&page_size=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1
        assert data["page_size"] == 1

    async def test_filter_by_name(
        self, admin_client: AsyncClient, admin_user: User, technician_user: User
    ):
        resp = await admin_client.get("/api/v1/users?name=Admin")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all("admin" in u["name"].lower() for u in items)

    async def test_technician_cannot_list_users(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/users")
        assert resp.status_code == 403


class TestGetUser:
    async def test_admin_gets_user_detail(self, admin_client: AsyncClient, admin_user: User):
        resp = await admin_client.get(f"/api/v1/users/{admin_user.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(admin_user.id)
        assert len(data["roles"]) > 0

    async def test_unknown_id_returns_404(self, admin_client: AsyncClient):
        from uuid import uuid4

        resp = await admin_client.get(f"/api/v1/users/{uuid4()}")
        assert resp.status_code == 404


class TestUpdateUser:
    async def test_admin_updates_user_name(self, admin_client: AsyncClient, technician_user: User):
        resp = await admin_client.patch(
            f"/api/v1/users/{technician_user.id}",
            json={"name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_email_conflict_on_update_returns_409(
        self, admin_client: AsyncClient, technician_user: User, admin_user: User
    ):
        resp = await admin_client.patch(
            f"/api/v1/users/{technician_user.id}",
            json={"email": "admin@test.com"},
        )
        assert resp.status_code == 409


class TestActivateDeactivate:
    async def test_deactivate_and_activate(self, admin_client: AsyncClient, technician_user: User):
        resp = await admin_client.post(f"/api/v1/users/{technician_user.id}/deactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        resp = await admin_client.post(f"/api/v1/users/{technician_user.id}/activate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    async def test_deactivating_last_admin_returns_422(
        self, admin_client: AsyncClient, admin_user: User
    ):
        resp = await admin_client.post(f"/api/v1/users/{admin_user.id}/deactivate")
        assert resp.status_code == 422


class TestRoleAssignment:
    async def test_assign_role_to_user(
        self,
        admin_client: AsyncClient,
        technician_user: User,
        admin_role,
    ):
        resp = await admin_client.post(
            f"/api/v1/users/{technician_user.id}/roles",
            json={"role_id": str(admin_role.id)},
        )
        assert resp.status_code == 200
        codes = [r["code"] for r in resp.json()]
        assert "admin" in codes
        assert "technician" in codes

    async def test_assign_duplicate_role_returns_409(
        self,
        admin_client: AsyncClient,
        admin_user: User,
        admin_role,
    ):
        resp = await admin_client.post(
            f"/api/v1/users/{admin_user.id}/roles",
            json={"role_id": str(admin_role.id)},
        )
        assert resp.status_code == 409

    async def test_remove_admin_role_from_last_admin_returns_422(
        self,
        admin_client: AsyncClient,
        admin_user: User,
        admin_role,
    ):
        resp = await admin_client.delete(f"/api/v1/users/{admin_user.id}/roles/{admin_role.id}")
        assert resp.status_code == 422


class TestRolesAndPermissions:
    async def test_list_roles_returns_default_roles(
        self, admin_client: AsyncClient, seeded_tenant: Tenant
    ):
        resp = await admin_client.get("/api/v1/roles")
        assert resp.status_code == 200
        codes = [r["code"] for r in resp.json()]
        assert "admin" in codes
        assert "supervisor" in codes
        assert "technician" in codes
        assert "requester" in codes

    async def test_list_permissions_requires_user_manage(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/permissions")
        assert resp.status_code == 403

    async def test_admin_lists_permissions(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/v1/permissions")
        assert resp.status_code == 200
        codes = [p["code"] for p in resp.json()]
        assert "user:manage" in codes
        assert "ticket:create" in codes


class TestGetMe:
    async def test_get_me_includes_permissions(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert "permissions" in data
        assert "user:manage" in data["permissions"]
        assert "roles" in data
        assert "admin" in data["roles"]

    async def test_get_me_technician_has_limited_permissions(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        perms = resp.json()["permissions"]
        assert "user:manage" not in perms
        assert "ticket:create" in perms


class TestSeed:
    async def test_seed_is_idempotent(self, db_session: AsyncSession, seeded_tenant: Tenant):
        from sqlalchemy import select

        from app.modules.users.models import Role
        from app.modules.users.seed import seed_default_roles_and_permissions

        await seed_default_roles_and_permissions(db_session, seeded_tenant.id)
        await db_session.flush()

        result = await db_session.execute(select(Role).where(Role.tenant_id == seeded_tenant.id))
        roles = result.scalars().all()
        codes = [r.code for r in roles]
        assert codes.count("admin") == 1
