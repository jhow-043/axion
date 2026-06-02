from __future__ import annotations

from httpx import AsyncClient

from app.modules.users.models import User


class TestLogin:
    async def test_login_valid_credentials_returns_access_token(
        self, auth_client: AsyncClient, active_user: User
    ):
        response = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "joao@empresa.com", "password": "senha123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_valid_sets_refresh_cookie(self, auth_client: AsyncClient, active_user: User):
        import asyncio

        async def _run():
            response = await auth_client.post(
                "/api/v1/auth/login",
                json={"email": "joao@empresa.com", "password": "senha123"},
            )
            assert response.status_code == 200
            assert "refresh_token" in response.cookies

        asyncio.get_event_loop().run_until_complete(_run())

    async def test_login_wrong_password_returns_401(
        self, auth_client: AsyncClient, active_user: User
    ):
        response = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "joao@empresa.com", "password": "errada"},
        )
        assert response.status_code == 401

    async def test_login_unknown_email_returns_401(self, auth_client: AsyncClient):
        response = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "ninguem@empresa.com", "password": "qualquer"},
        )
        assert response.status_code == 401

    async def test_login_wrong_password_and_unknown_email_same_message(
        self, auth_client: AsyncClient, active_user: User
    ):
        """Prevents user enumeration — messages must be identical (RN-02)."""
        r1 = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "joao@empresa.com", "password": "errada"},
        )
        r2 = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@empresa.com", "password": "qualquer"},
        )
        assert r1.status_code == 401
        assert r2.status_code == 401
        assert r1.json()["detail"] == r2.json()["detail"]

    async def test_login_inactive_user_returns_401(
        self, auth_client: AsyncClient, inactive_user: User
    ):
        response = await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "inativo@empresa.com", "password": "senha123"},
        )
        assert response.status_code == 401


class TestGetMe:
    async def test_get_me_with_valid_token_returns_user_data(
        self, authed_client: AsyncClient, active_user: User
    ):
        response = await authed_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "joao@empresa.com"
        assert data["name"] == "João Silva"
        assert "tenant_id" in data
        assert isinstance(data["roles"], list)
        assert "technician" in data["roles"]
        assert data["is_active"] is True

    async def test_get_me_without_token_returns_401(self, auth_client: AsyncClient):
        response = await auth_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_get_me_with_expired_token_returns_401(self, auth_client: AsyncClient):
        from datetime import UTC, datetime, timedelta

        from jose import jwt

        from app.core.config import settings

        expired_payload = {
            "sub": "00000000-0000-0000-0000-000000000000",
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "roles": [],
            "exp": datetime.now(UTC) - timedelta(seconds=1),
            "iat": datetime.now(UTC) - timedelta(minutes=1),
        }
        expired_token = jwt.encode(
            expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )
        response = await auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401


class TestRefresh:
    async def test_refresh_with_valid_cookie_returns_new_access_token(
        self, auth_client: AsyncClient, active_user: User
    ):
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "joao@empresa.com", "password": "senha123"},
        )

        refresh_response = await auth_client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_without_cookie_returns_401(self, auth_client: AsyncClient):
        response = await auth_client.post("/api/v1/auth/refresh")
        assert response.status_code == 401

    async def test_refresh_rotates_cookie(self, auth_client: AsyncClient, active_user: User):
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "joao@empresa.com", "password": "senha123"},
        )
        old_cookie = auth_client.cookies.get("refresh_token")

        await auth_client.post("/api/v1/auth/refresh")
        new_cookie = auth_client.cookies.get("refresh_token")

        assert old_cookie != new_cookie

    async def test_refresh_revoked_token_returns_401(
        self, auth_client: AsyncClient, active_user: User
    ):
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "joao@empresa.com", "password": "senha123"},
        )
        # First refresh consumes the cookie
        r1 = await auth_client.post("/api/v1/auth/refresh")
        assert r1.status_code == 200

        # Replace with a fake token to simulate using a revoked/unknown token
        auth_client.cookies.set("refresh_token", "fake_revoked_token_that_does_not_exist")
        r2 = await auth_client.post("/api/v1/auth/refresh")
        assert r2.status_code == 401


class TestLogout:
    async def test_logout_revokes_refresh_token(self, auth_client: AsyncClient, active_user: User):
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "joao@empresa.com", "password": "senha123"},
        )
        logout_response = await auth_client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 204

        refresh_response = await auth_client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == 401

    async def test_logout_clears_cookie(self, auth_client: AsyncClient, active_user: User):
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": "joao@empresa.com", "password": "senha123"},
        )
        assert auth_client.cookies.get("refresh_token") is not None

        await auth_client.post("/api/v1/auth/logout")
        assert auth_client.cookies.get("refresh_token") is None
