from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column


class TenantMixin:
    """Adds tenant_id to every domain model. INV-01: all data access scoped by tenant."""

    tenant_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
