from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.shared.tenant_mixin import TenantMixin


def _utcnow() -> datetime:
    return datetime.utcnow()


class AuditLog(TenantMixin, Base):
    """Append-only administrative audit trail (P17). INV-01: scoped by tenant."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    __table_args__ = (
        Index("ix_audit_logs_tenant_entity_type", "tenant_id", "entity_type"),
        Index("ix_audit_logs_tenant_actor", "tenant_id", "actor_id"),
        Index("ix_audit_logs_tenant_created_at", "tenant_id", "created_at"),
    )
