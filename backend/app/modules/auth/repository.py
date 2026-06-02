from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshToken
from app.modules.users.models import Permission, Role, RolePermission, User, UserRole


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class UserAuthRepository:
    """Read-only user lookups for the auth flow.
    No BaseRepository — tenant context does not exist yet at login time (ADR-0001 exception)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_role_codes(self, user_id: UUID) -> list[str]:
        stmt = (
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_permissions(self, user_id: UUID) -> list[str]:
        """Returns the union of permission codes from all roles assigned to the user."""
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class RefreshTokenRepository:
    """Manages refresh token lifecycle. No BaseRepository — no tenant_id column."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: UUID, token: str, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(
            user_id=user_id,
            token_hash=_hash_token(token),
            expires_at=expires_at,
        )
        self.session.add(rt)
        await self.session.flush()
        return rt

    async def find_valid(self, token: str) -> RefreshToken | None:
        """Returns token only if not revoked and not expired."""
        token_hash = _hash_token(token)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(UTC),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token_id: UUID) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(revoked_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revokes all tokens — called when a stolen token is detected (RN-05)."""
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
