"""Integration tests for P15 — Dashboards Operacionais.

Tests all three endpoints hitting real (SQLite) DB via HTTP."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Priority, Status
from app.modules.teams.models import Team
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import User

# ── Helpers ───────────────────────────────────────────────────────────────────


def _ticket(
    tenant_id,
    status_id,
    priority_id,
    requester_id,
    assignee_id=None,
    team_id=None,
    title="Chamado Teste",
):
    return Ticket(
        tenant_id=tenant_id,
        type="predial",
        title=title,
        description="Descrição de teste.",
        priority_id=priority_id,
        status_id=status_id,
        requester_id=requester_id,
        assignee_id=assignee_id,
        team_id=team_id,
    )


# ── GET /dashboards/technician ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_technician_dashboard_returns_own_tickets(
    tech_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    technician_user: User,
    admin_user: User,
    status_new: Status,
    status_in_progress: Status,
    default_priority: Priority,
    team: Team,
):
    db_session.add(
        _ticket(
            seeded_tenant.id,
            status_new.id,
            default_priority.id,
            admin_user.id,
            assignee_id=technician_user.id,
            team_id=team.id,
            title="Novo atribuído",
        )
    )
    db_session.add(
        _ticket(
            seeded_tenant.id,
            status_in_progress.id,
            default_priority.id,
            admin_user.id,
            assignee_id=technician_user.id,
            team_id=team.id,
            title="Em atendimento",
        )
    )
    # Ticket not assigned to this technician — must not appear
    db_session.add(
        _ticket(
            seeded_tenant.id,
            status_new.id,
            default_priority.id,
            admin_user.id,
            assignee_id=None,
            title="Não atribuído",
        )
    )
    await db_session.flush()

    resp = await tech_client.get("/api/v1/dashboards/technician")

    assert resp.status_code == 200
    data = resp.json()
    assert "assigned_tickets" in data
    assert data["assigned_tickets"]["total"] == 2
    assert data["assigned_tickets"]["by_status"]["new"] == 1
    assert data["assigned_tickets"]["by_status"]["in_progress"] == 1
    assert "sla_at_risk" in data
    assert "sla_breached" in data


@pytest.mark.asyncio
async def test_technician_dashboard_empty_when_no_assignments(
    tech_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    status_new: Status,
    default_priority: Priority,
):
    db_session.add(
        _ticket(seeded_tenant.id, status_new.id, default_priority.id, admin_user.id)
    )
    await db_session.flush()

    resp = await tech_client.get("/api/v1/dashboards/technician")

    assert resp.status_code == 200
    data = resp.json()
    assert data["assigned_tickets"]["total"] == 0
    assert data["assigned_tickets"]["by_status"] == {}


@pytest.mark.asyncio
async def test_technician_dashboard_requires_auth(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/dashboards/technician")
    assert resp.status_code == 401


# ── GET /dashboards/supervisor ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_supervisor_dashboard_shows_team_tickets(
    supervisor_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    supervisor_user: User,
    admin_user: User,
    status_new: Status,
    default_priority: Priority,
    team: Team,
):
    # Tickets in supervisor's team
    for _ in range(3):
        db_session.add(
            _ticket(
                seeded_tenant.id,
                status_new.id,
                default_priority.id,
                admin_user.id,
                team_id=team.id,
            )
        )
    # Ticket with no team — supervisor should not see it (not in their scope)
    db_session.add(
        _ticket(seeded_tenant.id, status_new.id, default_priority.id, admin_user.id)
    )
    await db_session.flush()

    resp = await supervisor_client.get("/api/v1/dashboards/supervisor")

    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_open"] == 3
    assert "teams" in data
    assert "sla_summary" in data
    # The team should appear in the teams list
    team_ids = [t["team_id"] for t in data["teams"]]
    assert str(team.id) in team_ids


@pytest.mark.asyncio
async def test_supervisor_dashboard_filters_by_team(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    status_new: Status,
    default_priority: Priority,
    team: Team,
):
    other_team = Team(tenant_id=seeded_tenant.id, name="Outra Equipe", is_active=True)
    db_session.add(other_team)
    await db_session.flush()

    db_session.add(
        _ticket(
            seeded_tenant.id, status_new.id, default_priority.id, admin_user.id, team_id=team.id
        )
    )
    db_session.add(
        _ticket(
            seeded_tenant.id,
            status_new.id,
            default_priority.id,
            admin_user.id,
            team_id=other_team.id,
        )
    )
    await db_session.flush()

    resp = await admin_client.get(f"/api/v1/dashboards/supervisor?team_id={team.id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_open"] == 1


@pytest.mark.asyncio
async def test_technician_cannot_access_supervisor_dashboard(
    tech_client: AsyncClient,
    seeded_tenant: Tenant,
):
    resp = await tech_client.get("/api/v1/dashboards/supervisor")
    assert resp.status_code == 403


# ── GET /dashboards/board ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_board_returns_columns_in_order(
    admin_client: AsyncClient,
    seeded_tenant: Tenant,
    db_session: AsyncSession,
    admin_user: User,
    status_new: Status,
    default_priority: Priority,
    team: Team,
):
    db_session.add(
        _ticket(
            seeded_tenant.id,
            status_new.id,
            default_priority.id,
            admin_user.id,
            team_id=team.id,
        )
    )
    await db_session.flush()

    resp = await admin_client.get("/api/v1/dashboards/board")

    assert resp.status_code == 200
    data = resp.json()
    assert "columns" in data
    columns = data["columns"]
    assert len(columns) > 0
    # Columns should not include "closed" (terminal status)
    codes = [c["status_code"] for c in columns]
    assert "closed" not in codes
    # Should include "new"
    assert "new" in codes
    # New column should have our ticket
    new_col = next(c for c in columns if c["status_code"] == "new")
    assert len(new_col["tickets"]) >= 1


@pytest.mark.asyncio
async def test_board_columns_have_correct_structure(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    status_new: Status,
    default_priority: Priority,
    team: Team,
):
    db_session.add(
        _ticket(
            seeded_tenant.id,
            status_new.id,
            default_priority.id,
            admin_user.id,
            team_id=team.id,
            title="Board card test",
        )
    )
    await db_session.flush()

    resp = await admin_client.get("/api/v1/dashboards/board")
    data = resp.json()

    new_col = next(c for c in data["columns"] if c["status_code"] == "new")
    ticket = next(t for t in new_col["tickets"] if t["title"] == "Board card test")
    assert "id" in ticket
    assert ticket["priority"] == "low"
    assert "assignee" in ticket
    assert "sla_status" in ticket


@pytest.mark.asyncio
async def test_board_filter_by_team(
    supervisor_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    supervisor_user: User,
    admin_user: User,
    status_new: Status,
    default_priority: Priority,
    team: Team,
):
    other_team = Team(tenant_id=seeded_tenant.id, name="Equipe B", is_active=True)
    db_session.add(other_team)
    await db_session.flush()

    # Ticket in supervisor's team
    db_session.add(
        _ticket(
            seeded_tenant.id, status_new.id, default_priority.id, admin_user.id, team_id=team.id
        )
    )
    # Ticket in other team — supervisor cannot access
    db_session.add(
        _ticket(
            seeded_tenant.id,
            status_new.id,
            default_priority.id,
            admin_user.id,
            team_id=other_team.id,
        )
    )
    await db_session.flush()

    resp = await supervisor_client.get("/api/v1/dashboards/board")

    assert resp.status_code == 200
    # Supervisor sees only their team's tickets
    all_tickets = [t for col in resp.json()["columns"] for t in col["tickets"]]
    assert len(all_tickets) == 1


@pytest.mark.asyncio
async def test_technician_cannot_access_board(tech_client: AsyncClient):
    resp = await tech_client.get("/api/v1/dashboards/board")
    assert resp.status_code == 403


# ── P16 — GET /dashboards/management ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_management_dashboard_returns_indicators(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    default_priority: Priority,
    status_new: Status,
    team: Team,
):
    from datetime import datetime, timedelta

    from sqlalchemy import select

    from app.modules.catalog.models import Status as St

    now = datetime.utcnow()
    result = await db_session.execute(
        select(St).where(St.tenant_id == seeded_tenant.id, St.code == "closed")
    )
    closed_st = result.scalar_one()

    for i in range(3):
        t = _ticket(seeded_tenant.id, status_new.id, default_priority.id, admin_user.id, team_id=team.id, title=f"T{i}")
        db_session.add(t)
    t_closed = _ticket(seeded_tenant.id, closed_st.id, default_priority.id, admin_user.id, team_id=team.id, title="Fechado")
    t_closed.closed_at = now - timedelta(hours=2)
    db_session.add(t_closed)
    await db_session.flush()

    # Use no date filter — router defaults to current month, which covers just-created tickets
    resp = await admin_client.get("/api/v1/dashboards/management")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "summary" in body
    assert "sla" in body
    assert "top_problematic_equipments" in body
    assert "team_performance" in body
    assert body["summary"]["total_tickets"] >= 4


@pytest.mark.asyncio
async def test_management_dashboard_technician_returns_403(tech_client: AsyncClient):
    resp = await tech_client.get("/api/v1/dashboards/management")
    assert resp.status_code == 403


# ── P16 — GET /reports/* ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_report_tickets_json(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    default_priority: "Priority",
    status_new: "Status",
    team: "Team",
):
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    t = _ticket(seeded_tenant.id, status_new.id, default_priority.id, admin_user.id, team_id=team.id)
    db_session.add(t)
    await db_session.flush()

    date_from = "2026-01-01T00:00:00"
    date_to = "2026-12-31T23:59:59"
    resp = await admin_client.get(
        f"/api/v1/reports/tickets?date_from={date_from}&date_to={date_to}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "priority" in data[0]


@pytest.mark.asyncio
async def test_report_tickets_csv(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    default_priority: "Priority",
    status_new: "Status",
    team: "Team",
):
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    t = _ticket(seeded_tenant.id, status_new.id, default_priority.id, admin_user.id, team_id=team.id)
    db_session.add(t)
    await db_session.flush()

    date_from = "2026-01-01T00:00:00"
    date_to = "2026-12-31T23:59:59"
    resp = await admin_client.get(
        f"/api/v1/reports/tickets?date_from={date_from}&date_to={date_to}&format=csv"
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment" in resp.headers["content-disposition"]
    content = resp.text
    assert "id" in content.splitlines()[0]


@pytest.mark.asyncio
async def test_report_tickets_missing_period_returns_422(admin_client: AsyncClient):
    resp = await admin_client.get("/api/v1/reports/tickets")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_report_tickets_period_over_limit_returns_422(admin_client: AsyncClient):
    date_from = "2020-01-01T00:00:00"
    date_to = "2021-03-10T00:00:00"
    resp = await admin_client.get(
        f"/api/v1/reports/tickets?date_from={date_from}&date_to={date_to}"
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_report_technician_returns_403(tech_client: AsyncClient):
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    date_from = "2026-01-01T00:00:00"
    date_to = "2026-12-31T23:59:59"
    resp = await tech_client.get(
        f"/api/v1/reports/tickets?date_from={date_from}&date_to={date_to}"
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_report_equipments_json(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    default_priority: "Priority",
    status_new: "Status",
):
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    date_from = "2026-01-01T00:00:00"
    date_to = "2026-12-31T23:59:59"
    resp = await admin_client.get(
        f"/api/v1/reports/equipments?date_from={date_from}&date_to={date_to}"
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_report_sla_json(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    default_priority: "Priority",
    status_new: "Status",
):
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    date_from = "2026-01-01T00:00:00"
    date_to = "2026-12-31T23:59:59"
    resp = await admin_client.get(
        f"/api/v1/reports/sla?date_from={date_from}&date_to={date_to}"
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_report_teams_json(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    default_priority: "Priority",
    status_new: "Status",
):
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    date_from = "2026-01-01T00:00:00"
    date_to = "2026-12-31T23:59:59"
    resp = await admin_client.get(
        f"/api/v1/reports/teams?date_from={date_from}&date_to={date_to}"
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
