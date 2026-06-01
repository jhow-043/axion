from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginationParams
from app.db.session import get_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


def get_pagination(
    page: int = Query(default=1, ge=1, description="Número da página (começa em 1)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Itens por página (máx. 100)"),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)
