from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.shared.tenant_mixin import TenantMixin


def _utcnow() -> datetime:
    # Use naive UTC — consistent with SQLite test behavior (DateTime() with aiosqlite)
    return datetime.utcnow()


class SlaPolicy(TenantMixin, Base):
    __tablename__ = "sla_policies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # 'industrial', 'predial', 'all'
    ticket_type: Mapped[str] = mapped_column(String(20), nullable=False)
    priority_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("priorities.id"), nullable=False)
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    attendance_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    alert_threshold_pct: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    __table_args__ = (
        # null-team uniqueness is enforced in service layer (SQLite/PG compat)
        UniqueConstraint(
            "tenant_id",
            "ticket_type",
            "priority_id",
            "team_id",
            name="uq_sla_policies_tenant_type_priority_team",
        ),
    )


class SlaTracker(TenantMixin, Base):
    __tablename__ = "sla_trackers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tickets.id"), unique=True, nullable=False
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sla_policies.id"), nullable=False)

    # SLA de Atendimento
    attendance_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attendance_status: Mapped[str] = mapped_column(String(10), default="running", nullable=False)
    attendance_met_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attendance_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # SLA de Resolução
    resolution_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_status: Mapped[str] = mapped_column(String(10), default="running", nullable=False)
    resolution_met_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    total_paused_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class SlaPause(TenantMixin, Base):
    __tablename__ = "sla_pauses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tracker_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sla_trackers.id"), nullable=False, index=True
    )
    paused_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
