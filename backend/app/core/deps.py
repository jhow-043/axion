from __future__ import annotations

from collections.abc import AsyncGenerator
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
