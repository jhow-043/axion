from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.modules.auth.repository import RefreshTokenRepository, UserAuthRepository
from app.modules.auth.schemas import TokenResponse, UserMeResponse
from app.modules.hub.repository import ModuleRepository
from app.modules.users.models import User

_INVALID_CREDENTIALS_MSG = "Email ou senha incorretos."


class AuthError(Exception):
    pass


class InvalidCredentialsError(AuthError):
    pass


class TokenRevokedError(AuthError):
    pass


class AuthService:
    def __init__(
        self,
        user_repo: UserAuthRepository,
        token_repo: RefreshTokenRepository,
        module_repo: ModuleRepository | None = None,
    ) -> None:
        self._users = user_repo
        self._tokens = token_repo
        self._modules = module_repo

    async def login(self, email: str, password: str) -> tuple[TokenResponse, str]:
        """Returns (TokenResponse, raw_refresh_token).
        Same error for all failures — prevents user enumeration (RN-02)."""
        user = await self._users.find_by_email(email)
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError(_INVALID_CREDENTIALS_MSG)

        roles = await self._users.get_role_codes(user.id)
        access_token = create_access_token(str(user.id), user.tenant_id, roles)
        raw_refresh = create_refresh_token()

        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._tokens.create(user.id, raw_refresh, expires_at)

        token_response = TokenResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return token_response, raw_refresh

    async def refresh(self, raw_refresh_token: str) -> tuple[TokenResponse, str]:
        """Rotates refresh token: revokes old, issues new pair.
        Raises TokenRevokedError if already revoked — signals possible token theft (RN-05)."""
        rt = await self._tokens.find_valid(raw_refresh_token)
        if rt is None:
            # Could be expired OR revoked — treat revoked as theft signal
            await self._handle_possible_theft(raw_refresh_token)
            raise TokenRevokedError("Refresh token inválido ou expirado.")

        await self._tokens.revoke(rt.id)

        user = await self._users.find_by_id(rt.user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError(_INVALID_CREDENTIALS_MSG)

        roles = await self._users.get_role_codes(user.id)
        access_token = create_access_token(str(user.id), user.tenant_id, roles)
        new_raw_refresh = create_refresh_token()

        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._tokens.create(user.id, new_raw_refresh, expires_at)

        token_response = TokenResponse(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        return token_response, new_raw_refresh

    async def logout(self, raw_refresh_token: str) -> None:
        rt = await self._tokens.find_valid(raw_refresh_token)
        if rt is not None:
            await self._tokens.revoke(rt.id)

    async def get_me(self, user: User) -> UserMeResponse:
        roles = await self._users.get_role_codes(user.id)
        permissions = await self._users.get_permissions(user.id)
        enabled_modules = (
            await self._modules.list_enabled_for_tenant(user.tenant_id)
            if self._modules is not None
            else []
        )
        return UserMeResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            tenant_id=user.tenant_id,
            roles=roles,
            permissions=permissions,
            enabled_modules=enabled_modules,
            is_active=user.is_active,
        )

    async def _handle_possible_theft(self, raw_token: str) -> None:
        """If an already-revoked token is presented, revoke ALL tokens for that user (RN-05)."""
        import hashlib

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        from sqlalchemy import select

        from app.modules.auth.models import RefreshToken

        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self._tokens.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is not None:
            await self._tokens.revoke_all_for_user(existing.user_id)

    @staticmethod
    def get_user_id_from_token_payload(payload: dict) -> UUID:
        return UUID(payload["sub"])

    @staticmethod
    def get_tenant_id_from_token_payload(payload: dict) -> UUID:
        return UUID(payload["tenant_id"])
