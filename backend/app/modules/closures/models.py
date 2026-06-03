from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.shared.tenant_mixin import TenantMixin


def _utcnow() -> datetime:
    return datetime.utcnow()


class Validation(TenantMixin, Base):
    __tablename__ = "validations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tickets.id"), nullable=False, unique=True
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 'pending', 'approved', 'rejected'
    status: Mapped[str] = mapped_column(String(10), default="pending", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    responded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=_utcnow, nullable=False)


class TenantSettings(Base):
    """One row per tenant — not using TenantMixin so tenant_id can be UNIQUE."""

    __tablename__ = "tenant_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id"), nullable=False, unique=True, index=True
    )
    auto_close_days: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), default=_utcnow, onupdate=_utcnow, nullable=False
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "auto_close_days BETWEEN 1 AND 90", name="ck_tenant_settings_auto_close_days"
        ),
    )
