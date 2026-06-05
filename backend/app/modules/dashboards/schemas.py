from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SlaRiskTicket(BaseModel):
    ticket_id: UUID
    title: str
    sla_type: str  # "attendance" | "resolution"
    due_at: datetime


class SlaBreachedTicket(BaseModel):
    ticket_id: UUID
    title: str
    sla_type: str
    breached_at: datetime


class AssignedTicketsSummary(BaseModel):
    total: int
    by_status: dict[str, int]


class TechnicianDashboardResponse(BaseModel):
    assigned_tickets: AssignedTicketsSummary
    sla_at_risk: list[SlaRiskTicket]
    sla_breached: list[SlaBreachedTicket]


class TeamSlaStats(BaseModel):
    team_id: UUID
    team_name: str
    total_open: int
    sla_at_risk: int
    sla_breached: int


class SlaSummary(BaseModel):
    attendance_compliance_pct: int
    resolution_compliance_pct: int


class TicketsSummary(BaseModel):
    total_open: int
    by_status: dict[str, int]
    by_priority: dict[str, int]


class SupervisorDashboardResponse(BaseModel):
    summary: TicketsSummary
    teams: list[TeamSlaStats]
    sla_summary: SlaSummary


class BoardTicketItem(BaseModel):
    id: UUID
    title: str
    priority: str
    assignee: str | None
    sla_status: str | None


class BoardColumn(BaseModel):
    status_code: str
    status_name: str
    tickets: list[BoardTicketItem]


class BoardResponse(BaseModel):
    columns: list[BoardColumn]
