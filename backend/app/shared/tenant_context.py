from __future__ import annotations

from contextvars import ContextVar
from uuid import UUID

# Set by auth middleware (P03). Workers must NOT rely on this — use explicit tenant_id (INV-04).
current_tenant_id: ContextVar[UUID | None] = ContextVar("current_tenant_id", default=None)


def set_tenant(tenant_id: UUID) -> None:
    current_tenant_id.set(tenant_id)


def get_tenant() -> UUID | None:
    return current_tenant_id.get()
