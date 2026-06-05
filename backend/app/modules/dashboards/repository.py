from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select

from app.modules.catalog.models import Priority, Status
from app.modules.sla.models import SlaTracker
from app.modules.teams.models import Team, TeamMember
from app.modules.tickets.models import Ticket
from app.modules.users.models import User
from app.shared.base_repository import BaseRepository


class DashboardRepository(BaseRepository[Ticket]):
    __model__ = Ticket

    async def count_assigned_by_status(self, assignee_id: UUID) -> dict[str, int]:
        stmt = (
            select(Status.code, func.count(Ticket.id).label("cnt"))
            .join(Status, Ticket.status_id == Status.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                Status.tenant_id == self.tenant_id,
                Ticket.assignee_id == assignee_id,
                Status.is_terminal.is_(False),
            )
            .group_by(Status.code)
        )
        result = await self.session.execute(stmt)
        return {row.code: row.cnt for row in result}

    async def list_sla_at_risk_for_user(
        self, user_id: UUID, threshold_minutes: int = 60
    ) -> list[tuple]:
        threshold = datetime.utcnow() + timedelta(minutes=threshold_minutes)
        now = datetime.utcnow()
        stmt = (
            select(
                Ticket.id,
                Ticket.title,
                SlaTracker.attendance_status,
                SlaTracker.attendance_due_at,
                SlaTracker.resolution_status,
                SlaTracker.resolution_due_at,
            )
            .join(SlaTracker, SlaTracker.ticket_id == Ticket.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                SlaTracker.tenant_id == self.tenant_id,
                Ticket.assignee_id == user_id,
                or_(
                    and_(
                        SlaTracker.attendance_status == "running",
                        SlaTracker.attendance_due_at.is_not(None),
                        SlaTracker.attendance_due_at <= threshold,
                        SlaTracker.attendance_due_at >= now,
                    ),
                    and_(
                        SlaTracker.resolution_status == "running",
                        SlaTracker.resolution_due_at.is_not(None),
                        SlaTracker.resolution_due_at <= threshold,
                        SlaTracker.resolution_due_at >= now,
                    ),
                ),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def list_sla_breached_for_user(self, user_id: UUID) -> list[tuple]:
        stmt = (
            select(
                Ticket.id,
                Ticket.title,
                SlaTracker.attendance_status,
                SlaTracker.attendance_due_at,
                SlaTracker.resolution_status,
                SlaTracker.resolution_due_at,
            )
            .join(SlaTracker, SlaTracker.ticket_id == Ticket.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                SlaTracker.tenant_id == self.tenant_id,
                Ticket.assignee_id == user_id,
                or_(
                    SlaTracker.attendance_status == "breached",
                    SlaTracker.resolution_status == "breached",
                ),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_open_ticket_summary(
        self,
        team_ids: list[UUID] | None,
        priority_id: UUID | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> tuple[dict[str, int], dict[str, int], int]:
        """Returns (by_status, by_priority, total_open) for non-terminal tickets."""
        stmt = (
            select(
                Status.code.label("sc"),
                Priority.code.label("pc"),
                func.count(Ticket.id).label("cnt"),
            )
            .join(Status, Ticket.status_id == Status.id)
            .join(Priority, Ticket.priority_id == Priority.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                Status.tenant_id == self.tenant_id,
                Priority.tenant_id == self.tenant_id,
                Status.is_terminal.is_(False),
            )
        )
        if team_ids is not None:
            stmt = stmt.where(Ticket.team_id.in_(team_ids))
        if priority_id:
            stmt = stmt.where(Ticket.priority_id == priority_id)
        if date_from:
            stmt = stmt.where(Ticket.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Ticket.created_at <= date_to)
        stmt = stmt.group_by(Status.code, Priority.code)

        result = await self.session.execute(stmt)
        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        total = 0
        for row in result:
            by_status[row.sc] = by_status.get(row.sc, 0) + row.cnt
            by_priority[row.pc] = by_priority.get(row.pc, 0) + row.cnt
            total += row.cnt
        return by_status, by_priority, total

    async def get_open_counts_by_team(
        self,
        team_ids: list[UUID],
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> dict[UUID, int]:
        stmt = (
            select(Ticket.team_id, func.count(Ticket.id).label("cnt"))
            .join(Status, Ticket.status_id == Status.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                Status.tenant_id == self.tenant_id,
                Status.is_terminal.is_(False),
                Ticket.team_id.in_(team_ids),
            )
        )
        if date_from:
            stmt = stmt.where(Ticket.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Ticket.created_at <= date_to)
        stmt = stmt.group_by(Ticket.team_id)
        result = await self.session.execute(stmt)
        return {row.team_id: row.cnt for row in result}

    async def get_sla_at_risk_counts_by_team(
        self, team_ids: list[UUID], threshold_minutes: int = 60
    ) -> dict[UUID, int]:
        threshold = datetime.utcnow() + timedelta(minutes=threshold_minutes)
        now = datetime.utcnow()
        stmt = (
            select(Ticket.team_id, func.count(Ticket.id).label("cnt"))
            .join(SlaTracker, SlaTracker.ticket_id == Ticket.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                SlaTracker.tenant_id == self.tenant_id,
                Ticket.team_id.in_(team_ids),
                or_(
                    and_(
                        SlaTracker.attendance_status == "running",
                        SlaTracker.attendance_due_at.is_not(None),
                        SlaTracker.attendance_due_at <= threshold,
                        SlaTracker.attendance_due_at >= now,
                    ),
                    and_(
                        SlaTracker.resolution_status == "running",
                        SlaTracker.resolution_due_at.is_not(None),
                        SlaTracker.resolution_due_at <= threshold,
                        SlaTracker.resolution_due_at >= now,
                    ),
                ),
            )
            .group_by(Ticket.team_id)
        )
        result = await self.session.execute(stmt)
        return {row.team_id: row.cnt for row in result}

    async def get_sla_breached_counts_by_team(self, team_ids: list[UUID]) -> dict[UUID, int]:
        stmt = (
            select(Ticket.team_id, func.count(Ticket.id).label("cnt"))
            .join(SlaTracker, SlaTracker.ticket_id == Ticket.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                SlaTracker.tenant_id == self.tenant_id,
                Ticket.team_id.in_(team_ids),
                or_(
                    SlaTracker.attendance_status == "breached",
                    SlaTracker.resolution_status == "breached",
                ),
            )
            .group_by(Ticket.team_id)
        )
        result = await self.session.execute(stmt)
        return {row.team_id: row.cnt for row in result}

    async def get_sla_compliance(
        self,
        team_ids: list[UUID] | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> tuple[int, int]:
        """Returns (attendance_compliance_pct, resolution_compliance_pct).
        Uses case() for SQLite compatibility in tests."""
        stmt = (
            select(
                func.sum(
                    case((SlaTracker.attendance_due_at.is_not(None), 1), else_=0)
                ).label("att_total"),
                func.sum(
                    case((SlaTracker.attendance_status == "met", 1), else_=0)
                ).label("att_met"),
                func.sum(
                    case((SlaTracker.resolution_due_at.is_not(None), 1), else_=0)
                ).label("res_total"),
                func.sum(
                    case((SlaTracker.resolution_status == "met", 1), else_=0)
                ).label("res_met"),
            )
            .join(Ticket, Ticket.id == SlaTracker.ticket_id)
            .where(
                SlaTracker.tenant_id == self.tenant_id,
                Ticket.tenant_id == self.tenant_id,
            )
        )
        if team_ids is not None:
            stmt = stmt.where(Ticket.team_id.in_(team_ids))
        if date_from:
            stmt = stmt.where(Ticket.created_at >= date_from)
        if date_to:
            stmt = stmt.where(Ticket.created_at <= date_to)

        result = await self.session.execute(stmt)
        row = result.one()
        att_total = row.att_total or 0
        att_met = row.att_met or 0
        res_total = row.res_total or 0
        res_met = row.res_met or 0

        att_pct = round(att_met / att_total * 100) if att_total > 0 else 100
        res_pct = round(res_met / res_total * 100) if res_total > 0 else 100
        return att_pct, res_pct

    async def get_non_terminal_statuses(self) -> list[Status]:
        stmt = (
            select(Status)
            .where(
                Status.tenant_id == self.tenant_id,
                Status.is_terminal.is_(False),
                Status.is_active.is_(True),
            )
            .order_by(Status.order)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_board_ticket_rows(
        self,
        team_ids: list[UUID] | None,
        assignee_id: UUID | None,
        priority_id: UUID | None,
    ) -> list[tuple]:
        """Returns rows with status, priority, assignee and SLA info for the Kanban board."""
        stmt = (
            select(
                Ticket.id,
                Ticket.title,
                Status.code.label("status_code"),
                Status.name.label("status_name"),
                Status.order.label("status_order"),
                Priority.code.label("priority_code"),
                User.name.label("assignee_name"),
                SlaTracker.attendance_status,
                SlaTracker.resolution_status,
            )
            .join(Status, Ticket.status_id == Status.id)
            .join(Priority, Ticket.priority_id == Priority.id)
            .outerjoin(User, Ticket.assignee_id == User.id)
            .outerjoin(SlaTracker, SlaTracker.ticket_id == Ticket.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                Status.tenant_id == self.tenant_id,
                Priority.tenant_id == self.tenant_id,
                Status.is_terminal.is_(False),
            )
        )
        if team_ids is not None:
            stmt = stmt.where(Ticket.team_id.in_(team_ids))
        if assignee_id:
            stmt = stmt.where(Ticket.assignee_id == assignee_id)
        if priority_id:
            stmt = stmt.where(Ticket.priority_id == priority_id)
        stmt = stmt.order_by(Status.order, Ticket.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_teams_by_ids(self, team_ids: list[UUID]) -> list[Team]:
        if not team_ids:
            return []
        stmt = (
            select(Team)
            .where(
                Team.tenant_id == self.tenant_id,
                Team.id.in_(team_ids),
                Team.is_active.is_(True),
            )
            .order_by(Team.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_active_teams(self) -> list[Team]:
        stmt = (
            select(Team)
            .where(
                Team.tenant_id == self.tenant_id,
                Team.is_active.is_(True),
            )
            .order_by(Team.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_team_ids(self, user_id: UUID) -> list[UUID]:
        stmt = select(TeamMember.team_id).where(
            TeamMember.user_id == user_id,
            TeamMember.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
