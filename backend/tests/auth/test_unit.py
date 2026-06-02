from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.modules.auth.service import (
    AuthService,
    InvalidCredentialsError,
    TokenRevokedError,
)


class TestPasswordHashing:
    def test_verify_correct_password(self):
        hashed = hash_password("secret")
        assert verify_password("secret", hashed) is True

    def test_reject_wrong_password(self):
        hashed = hash_password("secret")
        assert verify_password("wrong", hashed) is False

    def test_hashes_are_not_equal_to_plain(self):
        plain = "mypassword"
        assert hash_password(plain) != plain

    def test_two_hashes_of_same_password_are_different(self):
        # Argon2 uses random salt
        assert hash_password("same") != hash_password("same")


class TestJwtTokens:
    def test_create_access_token_has_correct_payload(self):
        user_id = str(uuid4())
        tenant_id = uuid4()
        roles = ["admin", "supervisor"]

        token = create_access_token(user_id, tenant_id, roles)
        payload = decode_access_token(token)

        assert payload["sub"] == user_id
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["roles"] == roles

    def test_access_token_expires_at_configured_time(self):
        token = create_access_token(str(uuid4()), uuid4(), [])
        payload = decode_access_token(token)
        delta = payload["exp"] - payload["iat"]
        assert delta == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def test_decode_expired_token_raises(self):
        from jose import jwt as _jwt

        payload = {
            "sub": str(uuid4()),
            "tenant_id": str(uuid4()),
            "roles": [],
            "exp": datetime.now(UTC) - timedelta(seconds=1),
            "iat": datetime.now(UTC) - timedelta(minutes=1),
        }
        token = _jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_access_token(token)

    def test_decode_tampered_token_raises(self):
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_access_token("not.a.valid.jwt")

    def test_refresh_token_is_opaque_and_unique(self):
        t1 = create_refresh_token()
        t2 = create_refresh_token()
        assert t1 != t2
        assert len(t1) > 32


class TestAuthServiceLogin:
    def _make_service(self, user=None, roles=None, existing_token=None):
        user_repo = AsyncMock()
        token_repo = AsyncMock()
        token_repo.session = MagicMock()

        if user is not None:
            user_repo.find_by_email.return_value = user
            user_repo.get_role_codes.return_value = roles or []
        else:
            user_repo.find_by_email.return_value = None

        return AuthService(user_repo, token_repo)

    def _make_user(self, *, is_active=True, password="secret"):
        user = MagicMock()
        user.id = uuid4()
        user.tenant_id = uuid4()
        user.is_active = is_active
        user.password_hash = hash_password(password)
        return user

    async def test_login_valid_credentials_returns_tokens(self):
        user = self._make_user()
        svc = self._make_service(user=user, roles=["technician"])

        token_resp, raw_refresh = await svc.login("x@y.com", "secret")

        assert token_resp.access_token
        assert token_resp.token_type == "bearer"
        assert raw_refresh

    async def test_login_wrong_password_raises(self):
        user = self._make_user(password="correct")
        svc = self._make_service(user=user)

        with pytest.raises(InvalidCredentialsError):
            await svc.login("x@y.com", "wrong")

    async def test_login_unknown_email_raises(self):
        svc = self._make_service(user=None)

        with pytest.raises(InvalidCredentialsError):
            await svc.login("ghost@y.com", "any")

    async def test_login_inactive_user_raises(self):
        user = self._make_user(is_active=False)
        svc = self._make_service(user=user)

        with pytest.raises(InvalidCredentialsError):
            await svc.login("x@y.com", "secret")

    async def test_login_error_messages_are_identical(self):
        """Same message regardless of email-exists or not — prevents user enumeration (RN-02)."""
        user = self._make_user(password="correct")
        svc_wrong_pw = self._make_service(user=user)
        svc_no_user = self._make_service(user=None)

        with pytest.raises(InvalidCredentialsError) as exc_wrong:
            await svc_wrong_pw.login("x@y.com", "bad")
        with pytest.raises(InvalidCredentialsError) as exc_no_user:
            await svc_no_user.login("ghost@y.com", "any")

        assert str(exc_wrong.value) == str(exc_no_user.value)


class TestAuthServiceRefresh:
    def _make_service(self, rt=None, user=None, roles=None):
        user_repo = AsyncMock()
        token_repo = AsyncMock()
        token_repo.session = MagicMock()

        token_repo.find_valid.return_value = rt
        if user is not None:
            user_repo.find_by_id.return_value = user
            user_repo.get_role_codes.return_value = roles or []

        # Simulate theft detection: no stored token matching the raw token

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        token_repo.session.execute = AsyncMock(return_value=mock_result)

        return AuthService(user_repo, token_repo)

    def _make_rt(self, *, user_id=None):
        rt = MagicMock()
        rt.id = uuid4()
        rt.user_id = user_id or uuid4()
        return rt

    def _make_user(self):
        user = MagicMock()
        user.id = uuid4()
        user.tenant_id = uuid4()
        user.is_active = True
        user.password_hash = hash_password("x")
        return user

    async def test_refresh_valid_token_rotates(self):
        user = self._make_user()
        rt = self._make_rt(user_id=user.id)
        svc = self._make_service(rt=rt, user=user, roles=["admin"])

        token_resp, new_raw = await svc.refresh("valid_raw_token")

        assert token_resp.access_token
        assert new_raw

    async def test_refresh_revoked_token_raises(self):
        svc = self._make_service(rt=None)

        with pytest.raises(TokenRevokedError):
            await svc.refresh("revoked_token")
