from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID

# Set by auth middleware (P03). Workers must NOT use this directly — use tenant_context() (INV-04).
current_tenant_id: ContextVar[UUID | None] = ContextVar("current_tenant_id", default=None)


def set_tenant(tenant_id: UUID) -> None:
    current_tenant_id.set(tenant_id)


def get_tenant() -> UUID | None:
    return current_tenant_id.get()


@contextmanager
def tenant_context(tenant_id: UUID) -> Generator[None, None, None]:
    """Context manager for Celery workers (INV-04). Token reset prevents leakage between tasks."""
    token = current_tenant_id.set(tenant_id)
    try:
        yield
    finally:
        current_tenant_id.reset(token)
