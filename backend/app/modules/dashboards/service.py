from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.core.exceptions import ForbiddenError
from app.modules.dashboards.repository import DashboardRepository
from app.modules.dashboards.schemas import (
    AssignedTicketsSummary,
    BoardColumn,
    BoardResponse,
    BoardTicketItem,
    SlaBreachedTicket,
    SlaRiskTicket,
    SlaSummary,
    SupervisorDashboardResponse,
    TeamSlaStats,
    TechnicianDashboardResponse,
    TicketsSummary,
)

_SUPERVISOR_ROLES = frozenset({"admin", "supervisor"})



def _compute_sla_status(
    attendance_status: str | None, resolution_status: str | None
) -> str | None:
    statuses = {s for s in (attendance_status, resolution_status) if s is not None}
    if not statuses:
        return None
    if "breached" in statuses:
        return "breached"
    if "running" in statuses:
        return "running"
    return "met"


def _build_sla_risk_list(rows: list[tuple]) -> list[SlaRiskTicket]:
    items: list[SlaRiskTicket] = []
    for row in rows:
        if row.attendance_status == "running" and row.attendance_due_at is not None:
            items.append(
                SlaRiskTicket(
                    ticket_id=row.id,
                    title=row.title,
                    sla_type="attendance",
                    due_at=row.attendance_due_at,
                )
            )
        if row.resolution_status == "running" and row.resolution_due_at is not None:
            items.append(
                SlaRiskTicket(
                    ticket_id=row.id,
                    title=row.title,
                    sla_type="resolution",
                    due_at=row.resolution_due_at,
                )
            )
    return items


def _build_sla_breached_list(rows: list[tuple]) -> list[SlaBreachedTicket]:
    items: list[SlaBreachedTicket] = []
    for row in rows:
        if row.attendance_status == "breached" and row.attendance_due_at is not None:
            items.append(
                SlaBreachedTicket(
                    ticket_id=row.id,
                    title=row.title,
                    sla_type="attendance",
                    breached_at=row.attendance_due_at,
                )
            )
        if row.resolution_status == "breached" and row.resolution_due_at is not None:
            items.append(
                SlaBreachedTicket(
                    ticket_id=row.id,
                    title=row.title,
                    sla_type="resolution",
                    breached_at=row.resolution_due_at,
                )
            )
    return items


class DashboardService:
    def __init__(self, dashboard_repo: DashboardRepository) -> None:
        self._repo = dashboard_repo

    async def get_technician_dashboard(
        self, user_id: UUID
    ) -> TechnicianDashboardResponse:
        by_status = await self._repo.count_assigned_by_status(user_id)
        at_risk_rows = await self._repo.list_sla_at_risk_for_user(user_id)
        breached_rows = await self._repo.list_sla_breached_for_user(user_id)

        return TechnicianDashboardResponse(
            assigned_tickets=AssignedTicketsSummary(
                total=sum(by_status.values()),
                by_status=by_status,
            ),
            sla_at_risk=_build_sla_risk_list(at_risk_rows),
            sla_breached=_build_sla_breached_list(breached_rows),
        )

    async def get_supervisor_dashboard(
        self,
        user_id: UUID,
        role_codes: list[str],
        team_id: UUID | None,
        priority_id: UUID | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> SupervisorDashboardResponse:
        if not any(r in _SUPERVISOR_ROLES for r in role_codes):
            raise ForbiddenError("Acesso restrito a supervisores e administradores.")

        scope_team_ids = await self._resolve_team_scope(user_id, role_codes, team_id)

        by_status, by_priority, total_open = await self._repo.get_open_ticket_summary(
            team_ids=scope_team_ids,
            priority_id=priority_id,
            date_from=date_from,
            date_to=date_to,
        )
        teams_stats = await self._build_team_stats(scope_team_ids, date_from, date_to)
        att_pct, res_pct = await self._repo.get_sla_compliance(
            team_ids=scope_team_ids,
            date_from=date_from,
            date_to=date_to,
        )

        return SupervisorDashboardResponse(
            summary=TicketsSummary(
                total_open=total_open,
                by_status=by_status,
                by_priority=by_priority,
            ),
            teams=teams_stats,
            sla_summary=SlaSummary(
                attendance_compliance_pct=att_pct,
                resolution_compliance_pct=res_pct,
            ),
        )

    async def get_board(
        self,
        user_id: UUID,
        role_codes: list[str],
        team_id: UUID | None,
        assignee_id: UUID | None,
        priority_id: UUID | None,
    ) -> BoardResponse:
        if not any(r in _SUPERVISOR_ROLES for r in role_codes):
            raise ForbiddenError("Acesso restrito a supervisores e administradores.")

        scope_team_ids = await self._resolve_team_scope(user_id, role_codes, team_id)
        ticket_rows = await self._repo.get_board_ticket_rows(
            team_ids=scope_team_ids,
            assignee_id=assignee_id,
            priority_id=priority_id,
        )
        statuses = await self._repo.get_non_terminal_statuses()

        columns_map: dict[str, list[BoardTicketItem]] = {s.code: [] for s in statuses}
        for row in ticket_rows:
            sla_status = _compute_sla_status(row.attendance_status, row.resolution_status)
            item = BoardTicketItem(
                id=row.id,
                title=row.title,
                priority=row.priority_code,
                assignee=row.assignee_name,
                sla_status=sla_status,
            )
            if row.status_code in columns_map:
                columns_map[row.status_code].append(item)

        columns = [
            BoardColumn(
                status_code=s.code,
                status_name=s.name,
                tickets=columns_map.get(s.code, []),
            )
            for s in statuses
        ]
        return BoardResponse(columns=columns)

    async def _resolve_team_scope(
        self,
        user_id: UUID,
        role_codes: list[str],
        filter_team_id: UUID | None,
    ) -> list[UUID] | None:
        """Returns None (all teams) for admin, or a list of team_ids for supervisor scope."""
        if "admin" in role_codes:
            if filter_team_id is not None:
                return [filter_team_id]
            return None

        # Supervisor scope: only teams they belong to
        user_team_ids = await self._repo.get_user_team_ids(user_id)
        if filter_team_id is not None:
            if filter_team_id not in user_team_ids:
                raise ForbiddenError("Equipe não pertence ao escopo do supervisor.")
            return [filter_team_id]
        return user_team_ids

    async def _build_team_stats(
        self,
        team_ids: list[UUID] | None,
        date_from: datetime | None,
        date_to: datetime | None,
    ) -> list[TeamSlaStats]:
        if team_ids is not None and not team_ids:
            return []

        if team_ids is None:
            teams = await self._repo.get_all_active_teams()
        else:
            teams = await self._repo.get_teams_by_ids(team_ids)

        if not teams:
            return []

        ids = [t.id for t in teams]
        open_counts = await self._repo.get_open_counts_by_team(ids, date_from, date_to)
        at_risk_counts = await self._repo.get_sla_at_risk_counts_by_team(ids)
        breached_counts = await self._repo.get_sla_breached_counts_by_team(ids)

        return [
            TeamSlaStats(
                team_id=t.id,
                team_name=t.name,
                total_open=open_counts.get(t.id, 0),
                sla_at_risk=at_risk_counts.get(t.id, 0),
                sla_breached=breached_counts.get(t.id, 0),
            )
            for t in teams
        ]
