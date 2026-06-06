from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select

from app.modules.catalog.models import Priority, Status
from app.modules.equipments.models import Equipment
from app.modules.sla.models import SlaTracker
from app.modules.teams.models import Team, TeamMember
from app.modules.tickets.models import Ticket
from app.modules.users.models import User
from app.shared.base_repository import BaseRepository

_HIGH_CRITICALITY = frozenset({"high", "critical"})


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

    # ── P16 — Dashboard Gerencial ─────────────────────────────────────────────

    async def get_management_ticket_summary(
        self,
        date_from: datetime,
        date_to: datetime,
        team_id: UUID | None,
        priority_id: UUID | None,
        ticket_type: str | None,
    ) -> tuple[int, int, int, dict[str, int], dict[str, int], list[tuple]]:
        """Returns (total, open, closed, by_type, by_priority, closed_pairs).

        closed_pairs is a list of (created_at, closed_at) for avg_resolution calc.
        """
        base_where = [
            Ticket.tenant_id == self.tenant_id,
            Status.tenant_id == self.tenant_id,
            Priority.tenant_id == self.tenant_id,
            Ticket.created_at >= date_from,
            Ticket.created_at <= date_to,
        ]
        if team_id:
            base_where.append(Ticket.team_id == team_id)
        if priority_id:
            base_where.append(Ticket.priority_id == priority_id)
        if ticket_type:
            base_where.append(Ticket.type == ticket_type)

        stmt = (
            select(
                Ticket.type,
                Priority.code.label("pc"),
                Status.is_terminal,
                Ticket.created_at,
                Ticket.closed_at,
            )
            .join(Status, Ticket.status_id == Status.id)
            .join(Priority, Ticket.priority_id == Priority.id)
            .where(*base_where)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        total = len(rows)
        open_count = 0
        closed_count = 0
        by_type: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        closed_pairs: list[tuple] = []

        for row in rows:
            by_type[row.type] = by_type.get(row.type, 0) + 1
            by_priority[row.pc] = by_priority.get(row.pc, 0) + 1
            if row.is_terminal:
                closed_count += 1
                if row.created_at and row.closed_at:
                    closed_pairs.append((row.created_at, row.closed_at))
            else:
                open_count += 1

        return total, open_count, closed_count, by_type, by_priority, closed_pairs

    async def get_management_sla(
        self,
        date_from: datetime,
        date_to: datetime,
        team_id: UUID | None,
    ) -> tuple[int, int, int]:
        """Returns (attendance_compliance_pct, resolution_compliance_pct, breached_count)."""
        stmt = (
            select(
                SlaTracker.attendance_status,
                SlaTracker.attendance_due_at,
                SlaTracker.resolution_status,
                SlaTracker.resolution_due_at,
            )
            .join(Ticket, Ticket.id == SlaTracker.ticket_id)
            .where(
                SlaTracker.tenant_id == self.tenant_id,
                Ticket.tenant_id == self.tenant_id,
                Ticket.created_at >= date_from,
                Ticket.created_at <= date_to,
            )
        )
        if team_id:
            stmt = stmt.where(Ticket.team_id == team_id)

        result = await self.session.execute(stmt)
        rows = result.all()

        att_total = att_met = res_total = res_met = breached = 0
        for row in rows:
            if row.attendance_due_at is not None:
                att_total += 1
                if row.attendance_status == "met":
                    att_met += 1
                elif row.attendance_status == "breached":
                    breached += 1
            if row.resolution_due_at is not None:
                res_total += 1
                if row.resolution_status == "met":
                    res_met += 1
                elif row.resolution_status == "breached":
                    breached += 1

        att_pct = round(att_met / att_total * 100) if att_total > 0 else 100
        res_pct = round(res_met / res_total * 100) if res_total > 0 else 100
        return att_pct, res_pct, breached

    async def get_top_problematic_equipments(
        self,
        date_from: datetime,
        date_to: datetime,
        team_id: UUID | None,
        ticket_type: str | None,
        limit: int = 10,
    ) -> list[tuple]:
        """Returns list of (equipment_id, name, ticket_count, critical_count) sorted desc."""
        stmt = (
            select(
                Equipment.id,
                Equipment.name,
                Priority.code.label("pc"),
            )
            .join(Ticket, Ticket.equipment_id == Equipment.id)
            .join(Priority, Ticket.priority_id == Priority.id)
            .where(
                Equipment.tenant_id == self.tenant_id,
                Ticket.tenant_id == self.tenant_id,
                Priority.tenant_id == self.tenant_id,
                Ticket.equipment_id.is_not(None),
                Ticket.created_at >= date_from,
                Ticket.created_at <= date_to,
            )
        )
        if team_id:
            stmt = stmt.where(Ticket.team_id == team_id)
        if ticket_type:
            stmt = stmt.where(Ticket.type == ticket_type)

        result = await self.session.execute(stmt)
        rows = result.all()

        counts: dict[UUID, dict] = {}
        for row in rows:
            entry = counts.setdefault(row.id, {"name": row.name, "total": 0, "critical": 0})
            entry["total"] += 1
            if row.pc in _HIGH_CRITICALITY:
                entry["critical"] += 1

        sorted_items = sorted(
            counts.items(), key=lambda kv: (-kv[1]["total"], -kv[1]["critical"])
        )
        return [(eid, d["name"], d["total"], d["critical"]) for eid, d in sorted_items[:limit]]

    async def get_team_performance(
        self,
        date_from: datetime,
        date_to: datetime,
        team_id: UUID | None,
    ) -> list[tuple]:
        """Returns (team_id, team_name, total_closed, closed_pairs, att_pct, res_pct)."""
        stmt = (
            select(
                Team.id,
                Team.name,
                Ticket.created_at,
                Ticket.closed_at,
                SlaTracker.attendance_status,
                SlaTracker.attendance_due_at,
                SlaTracker.resolution_status,
                SlaTracker.resolution_due_at,
            )
            .join(Ticket, Ticket.team_id == Team.id)
            .join(Status, Ticket.status_id == Status.id)
            .outerjoin(SlaTracker, SlaTracker.ticket_id == Ticket.id)
            .where(
                Team.tenant_id == self.tenant_id,
                Ticket.tenant_id == self.tenant_id,
                Status.tenant_id == self.tenant_id,
                Status.is_terminal.is_(True),
                Ticket.closed_at >= date_from,
                Ticket.closed_at <= date_to,
            )
        )
        if team_id:
            stmt = stmt.where(Team.id == team_id)

        result = await self.session.execute(stmt)
        rows = result.all()

        teams: dict[UUID, dict] = {}
        for row in rows:
            entry = teams.setdefault(
                row.id,
                {
                    "name": row.name,
                    "closed_pairs": [],
                    "att_total": 0,
                    "att_met": 0,
                    "res_total": 0,
                    "res_met": 0,
                },
            )
            if row.created_at and row.closed_at:
                entry["closed_pairs"].append((row.created_at, row.closed_at))
            if row.attendance_due_at is not None:
                entry["att_total"] += 1
                if row.attendance_status == "met":
                    entry["att_met"] += 1
            if row.resolution_due_at is not None:
                entry["res_total"] += 1
                if row.resolution_status == "met":
                    entry["res_met"] += 1

        return [
            (
                tid,
                d["name"],
                len(d["closed_pairs"]),
                d["closed_pairs"],
                round(d["att_met"] / d["att_total"] * 100) if d["att_total"] > 0 else 100,
                round(d["res_met"] / d["res_total"] * 100) if d["res_total"] > 0 else 100,
            )
            for tid, d in teams.items()
        ]

    async def get_tickets_for_report(
        self,
        date_from: datetime,
        date_to: datetime,
        team_id: UUID | None,
        priority_id: UUID | None,
        ticket_type: str | None,
    ) -> list[tuple]:
        """Rows for the tickets CSV report."""
        stmt = (
            select(
                Ticket.id,
                Ticket.type,
                Ticket.title,
                Priority.code.label("priority"),
                Status.code.label("status"),
                Status.is_terminal,
                Ticket.created_at,
                Ticket.closed_at,
                Team.name.label("team_name"),
            )
            .join(Status, Ticket.status_id == Status.id)
            .join(Priority, Ticket.priority_id == Priority.id)
            .outerjoin(Team, Ticket.team_id == Team.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                Status.tenant_id == self.tenant_id,
                Priority.tenant_id == self.tenant_id,
                Ticket.created_at >= date_from,
                Ticket.created_at <= date_to,
            )
        )
        if team_id:
            stmt = stmt.where(Ticket.team_id == team_id)
        if priority_id:
            stmt = stmt.where(Ticket.priority_id == priority_id)
        if ticket_type:
            stmt = stmt.where(Ticket.type == ticket_type)
        stmt = stmt.order_by(Ticket.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_sla_for_report(
        self,
        date_from: datetime,
        date_to: datetime,
        team_id: UUID | None,
    ) -> list[tuple]:
        """Rows for the SLA CSV report."""
        stmt = (
            select(
                Ticket.id,
                Ticket.title,
                SlaTracker.attendance_due_at,
                SlaTracker.attendance_status,
                SlaTracker.resolution_due_at,
                SlaTracker.resolution_status,
                SlaTracker.total_paused_minutes,
                Ticket.created_at,
                Team.name.label("team_name"),
            )
            .join(SlaTracker, SlaTracker.ticket_id == Ticket.id)
            .outerjoin(Team, Ticket.team_id == Team.id)
            .where(
                Ticket.tenant_id == self.tenant_id,
                SlaTracker.tenant_id == self.tenant_id,
                Ticket.created_at >= date_from,
                Ticket.created_at <= date_to,
            )
        )
        if team_id:
            stmt = stmt.where(Ticket.team_id == team_id)
        stmt = stmt.order_by(Ticket.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_equipments_for_report(
        self,
        date_from: datetime,
        date_to: datetime,
    ) -> list[tuple]:
        """Rows for the equipments CSV report."""
        stmt = (
            select(
                Equipment.id,
                Equipment.code,
                Equipment.name,
                func.count(Ticket.id).label("ticket_count"),
                func.sum(
                    case((Priority.code.in_(list(_HIGH_CRITICALITY)), 1), else_=0)
                ).label("critical_count"),
            )
            .join(Ticket, Ticket.equipment_id == Equipment.id)
            .join(Priority, Ticket.priority_id == Priority.id)
            .where(
                Equipment.tenant_id == self.tenant_id,
                Ticket.tenant_id == self.tenant_id,
                Priority.tenant_id == self.tenant_id,
                Ticket.created_at >= date_from,
                Ticket.created_at <= date_to,
            )
            .group_by(Equipment.id, Equipment.code, Equipment.name)
            .order_by(func.count(Ticket.id).desc())
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_teams_for_report(
        self,
        date_from: datetime,
        date_to: datetime,
        team_id: UUID | None,
    ) -> list[tuple]:
        """Rows for the teams performance CSV report (closed tickets only)."""
        stmt = (
            select(
                Team.id,
                Team.name,
                func.count(Ticket.id).label("total_closed"),
            )
            .join(Ticket, Ticket.team_id == Team.id)
            .join(Status, Ticket.status_id == Status.id)
            .where(
                Team.tenant_id == self.tenant_id,
                Ticket.tenant_id == self.tenant_id,
                Status.tenant_id == self.tenant_id,
                Status.is_terminal.is_(True),
                Ticket.closed_at >= date_from,
                Ticket.closed_at <= date_to,
            )
        )
        if team_id:
            stmt = stmt.where(Team.id == team_id)
        stmt = stmt.group_by(Team.id, Team.name).order_by(Team.name)
        result = await self.session.execute(stmt)
        return list(result.all())
