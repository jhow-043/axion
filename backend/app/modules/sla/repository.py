from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_

from app.modules.sla.models import SlaPause, SlaPolicy, SlaTracker
from app.shared.base_repository import BaseRepository


class SlaPolicyRepository(BaseRepository[SlaPolicy]):
    __model__ = SlaPolicy

    async def find_applicable(
        self,
        *,
        ticket_type: str,
        priority_id: UUID,
        team_id: UUID | None,
    ) -> SlaPolicy | None:
        """Finds the most specific active policy (spec P12 policy selection order)."""
        if team_id is not None:
            stmt = self._base_query().where(
                SlaPolicy.ticket_type == ticket_type,
                SlaPolicy.priority_id == priority_id,
                SlaPolicy.team_id == team_id,
                SlaPolicy.is_active.is_(True),
            )
            result = await self.session.execute(stmt)
            policy = result.scalar_one_or_none()
            if policy is not None:
                return policy

        stmt = self._base_query().where(
            SlaPolicy.ticket_type == ticket_type,
            SlaPolicy.priority_id == priority_id,
            SlaPolicy.team_id.is_(None),
            SlaPolicy.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        policy = result.scalar_one_or_none()
        if policy is not None:
            return policy

        stmt = self._base_query().where(
            SlaPolicy.ticket_type == "all",
            SlaPolicy.priority_id == priority_id,
            SlaPolicy.team_id.is_(None),
            SlaPolicy.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_duplicate(
        self,
        *,
        ticket_type: str,
        priority_id: UUID,
        team_id: UUID | None,
        exclude_id: UUID | None = None,
    ) -> SlaPolicy | None:
        """Checks for an existing active policy with same key (null team_id included)."""
        stmt = self._base_query().where(
            SlaPolicy.ticket_type == ticket_type,
            SlaPolicy.priority_id == priority_id,
            SlaPolicy.team_id.is_(None) if team_id is None else SlaPolicy.team_id == team_id,
            SlaPolicy.is_active.is_(True),
        )
        if exclude_id is not None:
            stmt = stmt.where(SlaPolicy.id != exclude_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class SlaTrackerRepository(BaseRepository[SlaTracker]):
    __model__ = SlaTracker

    async def find_by_ticket(self, ticket_id: UUID) -> SlaTracker | None:
        stmt = self._base_query().where(SlaTracker.ticket_id == ticket_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_overdue(self) -> list[SlaTracker]:
        """Trackers where at least one running SLA has passed its deadline."""
        now = datetime.utcnow()
        stmt = self._base_query().where(
            or_(
                and_(
                    SlaTracker.attendance_status == "running",
                    SlaTracker.attendance_due_at.is_not(None),
                    SlaTracker.attendance_due_at < now,
                ),
                and_(
                    SlaTracker.resolution_status == "running",
                    SlaTracker.resolution_due_at.is_not(None),
                    SlaTracker.resolution_due_at < now,
                ),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_running(self) -> list[SlaTracker]:
        """Trackers with at least one SLA still running (for alert threshold sweep)."""
        stmt = self._base_query().where(
            or_(
                SlaTracker.attendance_status == "running",
                SlaTracker.resolution_status == "running",
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class SlaPauseRepository(BaseRepository[SlaPause]):
    __model__ = SlaPause

    async def find_open_pause(self, tracker_id: UUID) -> SlaPause | None:
        stmt = self._base_query().where(
            SlaPause.tracker_id == tracker_id,
            SlaPause.resumed_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
