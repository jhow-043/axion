from __future__ import annotations

from abc import ABC
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(ABC, Generic[ModelT]):  # noqa: UP046
    """
    Abstract base for all tenant-scoped repositories. Full implementation in P01.
    INV-01: every domain data access passes through this class.
    INV-02: get() with a cross-tenant ID returns None → router raises 404.
    """

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id
