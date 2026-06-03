from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from uuid import UUID

from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginationParams
from app.core.security import decode_access_token
from app.db.session import get_session_factory
from app.shared.tenant_context import get_tenant, set_tenant

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


def get_pagination(
    page: int = Query(default=1, ge=1, description="Número da página (começa em 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Itens por página (máx. 100)"),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """Validates Bearer token, sets tenant ContextVar (INV-01 / spec P03 RN-08).
    Returns the authenticated User ORM object."""
    # import here to avoid circular imports at module load time
    from app.modules.users.models import User

    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    user_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tenant_id"])

    # Set tenant ContextVar before any repository access (ADR-0001)
    set_tenant(tenant_id)

    stmt = select(User).where(
        User.id == user_id, User.tenant_id == tenant_id, User.is_active.is_(True)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo.")
    return user


async def get_current_tenant() -> UUID:
    """FastAPI dependency. Returns current tenant_id from ContextVar.
    Set by get_current_user() (P03). Raises 401 if context not set."""
    tenant_id = get_tenant()
    if tenant_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return tenant_id


def require_permission(permission_code: str) -> Callable:
    """Factory returning a FastAPI dependency that enforces a permission check.
    Raises 403 if the authenticated user does not hold the required permission.
    Permissions are resolved from the DB on every request — no stale JWT cache (spec RN)."""

    async def _check(
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        from app.modules.auth.repository import UserAuthRepository

        repo = UserAuthRepository(db)
        permissions = await repo.get_permissions(current_user.id)
        if permission_code not in permissions:
            raise HTTPException(status_code=403, detail="Permissão insuficiente.")
        return current_user

    return _check


async def get_current_role_codes(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """Returns role codes for the current user — used for visibility scoping."""
    from app.modules.auth.repository import UserAuthRepository

    repo = UserAuthRepository(db)
    return await repo.get_role_codes(current_user.id)


def require_any_permission(*permission_codes: str) -> Callable:
    """Factory returning a dependency that passes if the user holds ANY of the given permissions."""

    async def _check(
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        from app.modules.auth.repository import UserAuthRepository

        repo = UserAuthRepository(db)
        permissions = await repo.get_permissions(current_user.id)
        if not any(code in permissions for code in permission_codes):
            raise HTTPException(status_code=403, detail="Permissão insuficiente.")
        return current_user

    return _check
