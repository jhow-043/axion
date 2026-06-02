from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.tenant_mixin import TenantMixin


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Team(TenantMixin, Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow, nullable=False)

    members: Mapped[list[TeamMember]] = relationship(
        "TeamMember", back_populates="team", lazy="selectin"
    )

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_teams_tenant_name"),)


class TeamMember(TenantMixin, Base):
    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(default=_utcnow, nullable=False)

    team: Mapped[Team] = relationship("Team", back_populates="members")

    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),)
