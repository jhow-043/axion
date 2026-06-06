"""Unit tests for P15 — Dashboards Operacionais and P16 — Dashboard Gerencial.

Tests pure business logic without hitting the database."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ForbiddenError
from app.modules.dashboards.service import (
    DashboardService,
    _build_sla_breached_list,
    _build_sla_risk_list,
    _compute_sla_status,
)

# ── _compute_sla_status ───────────────────────────────────────────────────────


class TestComputeSlaStatus:
    def test_none_when_no_tracker(self):
        assert _compute_sla_status(None, None) is None

    def test_breached_wins_over_running(self):
        assert _compute_sla_status("breached", "running") == "breached"

    def test_running_when_no_breach(self):
        assert _compute_sla_status("running", "met") == "running"

    def test_met_when_both_met(self):
        assert _compute_sla_status("met", "met") == "met"

    def test_running_when_one_side_none(self):
        assert _compute_sla_status("running", None) == "running"

    def test_met_when_one_met_one_none(self):
        assert _compute_sla_status("met", None) == "met"


# ── _build_sla_risk_list ──────────────────────────────────────────────────────


class TestBuildSlaRiskList:
    def test_empty_rows_returns_empty(self):
        assert _build_sla_risk_list([]) == []

    def test_attendance_at_risk(self):
        due = datetime.utcnow() + timedelta(minutes=30)
        row = SimpleNamespace(
            id=uuid4(),
            title="Teste",
            attendance_status="running",
            attendance_due_at=due,
            resolution_status="running",
            resolution_due_at=None,
        )
        items = _build_sla_risk_list([row])
        assert len(items) == 1
        assert items[0].sla_type == "attendance"
        assert items[0].due_at == due

    def test_both_at_risk_produces_two_items(self):
        due1 = datetime.utcnow() + timedelta(minutes=20)
        due2 = datetime.utcnow() + timedelta(minutes=40)
        row = SimpleNamespace(
            id=uuid4(),
            title="Duplo",
            attendance_status="running",
            attendance_due_at=due1,
            resolution_status="running",
            resolution_due_at=due2,
        )
        items = _build_sla_risk_list([row])
        types = {i.sla_type for i in items}
        assert types == {"attendance", "resolution"}

    def test_met_status_not_included(self):
        row = SimpleNamespace(
            id=uuid4(),
            title="Met",
            attendance_status="met",
            attendance_due_at=datetime.utcnow(),
            resolution_status="met",
            resolution_due_at=datetime.utcnow(),
        )
        assert _build_sla_risk_list([row]) == []


# ── _build_sla_breached_list ──────────────────────────────────────────────────


class TestBuildSlaBreachedList:
    def test_empty_rows_returns_empty(self):
        assert _build_sla_breached_list([]) == []

    def test_attendance_breached(self):
        due = datetime.utcnow() - timedelta(hours=2)
        row = SimpleNamespace(
            id=uuid4(),
            title="Breach",
            attendance_status="breached",
            attendance_due_at=due,
            resolution_status="running",
            resolution_due_at=None,
        )
        items = _build_sla_breached_list([row])
        assert len(items) == 1
        assert items[0].sla_type == "attendance"
        assert items[0].breached_at == due

    def test_both_breached_produces_two_items(self):
        due = datetime.utcnow() - timedelta(hours=1)
        row = SimpleNamespace(
            id=uuid4(),
            title="Both",
            attendance_status="breached",
            attendance_due_at=due,
            resolution_status="breached",
            resolution_due_at=due,
        )
        items = _build_sla_breached_list([row])
        assert len(items) == 2

    def test_running_not_included(self):
        row = SimpleNamespace(
            id=uuid4(),
            title="Running",
            attendance_status="running",
            attendance_due_at=datetime.utcnow() + timedelta(hours=1),
            resolution_status="running",
            resolution_due_at=datetime.utcnow() + timedelta(hours=2),
        )
        assert _build_sla_breached_list([row]) == []


# ── Supervisor visibility check ───────────────────────────────────────────────


class TestSupervisorVisibility:
    """Technician calling supervisor dashboard must get ForbiddenError."""

    @pytest.mark.asyncio
    async def test_technician_raises_forbidden_on_supervisor(self):
        repo = AsyncMock()
        svc = DashboardService(dashboard_repo=repo)

        with pytest.raises(ForbiddenError):
            await svc.get_supervisor_dashboard(
                user_id=uuid4(),
                role_codes=["technician"],
                team_id=None,
                priority_id=None,
                date_from=None,
                date_to=None,
            )

    @pytest.mark.asyncio
    async def test_technician_raises_forbidden_on_board(self):
        repo = AsyncMock()
        svc = DashboardService(dashboard_repo=repo)

        with pytest.raises(ForbiddenError):
            await svc.get_board(
                user_id=uuid4(),
                role_codes=["technician"],
                team_id=None,
                assignee_id=None,
                priority_id=None,
            )

    @pytest.mark.asyncio
    async def test_requester_raises_forbidden_on_supervisor(self):
        repo = AsyncMock()
        svc = DashboardService(dashboard_repo=repo)

        with pytest.raises(ForbiddenError):
            await svc.get_supervisor_dashboard(
                user_id=uuid4(),
                role_codes=["requester"],
                team_id=None,
                priority_id=None,
                date_from=None,
                date_to=None,
            )


# ── SLA compliance percentage ─────────────────────────────────────────────────


class TestSlaComplianceCalc:
    """Validates compliance percentage formula: met / total * 100."""

    @pytest.mark.asyncio
    async def test_full_compliance_when_all_met(self):
        repo = AsyncMock()
        repo.get_open_ticket_summary = AsyncMock(return_value=({}, {}, 0))
        repo.get_all_active_teams = AsyncMock(return_value=[])
        repo.get_sla_compliance = AsyncMock(return_value=(100, 100))
        svc = DashboardService(dashboard_repo=repo)

        resp = await svc.get_supervisor_dashboard(
            user_id=uuid4(),
            role_codes=["admin"],
            team_id=None,
            priority_id=None,
            date_from=None,
            date_to=None,
        )

        assert resp.sla_summary.attendance_compliance_pct == 100
        assert resp.sla_summary.resolution_compliance_pct == 100

    @pytest.mark.asyncio
    async def test_partial_compliance_forwarded_correctly(self):
        repo = AsyncMock()
        repo.get_open_ticket_summary = AsyncMock(return_value=({"new": 2}, {"low": 2}, 2))
        repo.get_all_active_teams = AsyncMock(return_value=[])
        repo.get_sla_compliance = AsyncMock(return_value=(75, 50))
        svc = DashboardService(dashboard_repo=repo)

        resp = await svc.get_supervisor_dashboard(
            user_id=uuid4(),
            role_codes=["admin"],
            team_id=None,
            priority_id=None,
            date_from=None,
            date_to=None,
        )

        assert resp.sla_summary.attendance_compliance_pct == 75
        assert resp.sla_summary.resolution_compliance_pct == 50


# ── P16 — _avg_hours ──────────────────────────────────────────────────────────


class TestAvgHours:
    def test_empty_returns_zero(self):
        from app.modules.dashboards.service import _avg_hours

        assert _avg_hours([]) == 0.0

    def test_none_pairs_ignored(self):
        from app.modules.dashboards.service import _avg_hours

        assert _avg_hours([(None, None)]) == 0.0

    def test_single_pair_2h(self):
        from datetime import timedelta

        from app.modules.dashboards.service import _avg_hours

        t0 = datetime.utcnow()
        t1 = t0 + timedelta(hours=2)
        assert _avg_hours([(t0, t1)]) == 2.0

    def test_average_of_two_pairs(self):
        from datetime import timedelta

        from app.modules.dashboards.service import _avg_hours

        t0 = datetime.utcnow()
        assert _avg_hours([(t0, t0 + timedelta(hours=1)), (t0, t0 + timedelta(hours=3))]) == 2.0

    def test_strips_timezone(self):
        from datetime import timezone, timedelta

        from app.modules.dashboards.service import _avg_hours

        t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        t1 = t0 + timedelta(hours=4)
        assert _avg_hours([(t0, t1)]) == 4.0


# ── P16 — management dashboard access control ─────────────────────────────────


class TestManagementDashboardAccess:
    @pytest.mark.asyncio
    async def test_technician_raises_forbidden(self):
        from unittest.mock import AsyncMock

        from app.core.exceptions import ForbiddenError
        from app.modules.dashboards.service import DashboardService

        repo = AsyncMock()
        svc = DashboardService(dashboard_repo=repo)

        with pytest.raises(ForbiddenError):
            await svc.get_management_dashboard(
                role_codes=["technician"],
                date_from=datetime(2024, 1, 1),
                date_to=datetime(2024, 1, 31),
                team_id=None,
                priority_id=None,
                ticket_type=None,
            )

    @pytest.mark.asyncio
    async def test_admin_succeeds_with_empty_data(self):
        from unittest.mock import AsyncMock
        from uuid import uuid4

        from app.modules.dashboards.service import DashboardService

        repo = AsyncMock()
        repo.get_management_ticket_summary = AsyncMock(
            return_value=(0, 0, 0, {}, {}, [])
        )
        repo.get_management_sla = AsyncMock(return_value=(100, 100, 0))
        repo.get_top_problematic_equipments = AsyncMock(return_value=[])
        repo.get_team_performance = AsyncMock(return_value=[])
        svc = DashboardService(dashboard_repo=repo)

        resp = await svc.get_management_dashboard(
            role_codes=["admin"],
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 31),
            team_id=None,
            priority_id=None,
            ticket_type=None,
        )

        assert resp.summary.total_tickets == 0
        assert resp.sla.breached_count == 0
        assert resp.top_problematic_equipments == []
        assert resp.team_performance == []

    @pytest.mark.asyncio
    async def test_sla_compliance_forwarded(self):
        from unittest.mock import AsyncMock

        from app.modules.dashboards.service import DashboardService

        repo = AsyncMock()
        repo.get_management_ticket_summary = AsyncMock(
            return_value=(10, 5, 5, {"industrial": 10}, {"high": 10}, [])
        )
        repo.get_management_sla = AsyncMock(return_value=(80, 60, 3))
        repo.get_top_problematic_equipments = AsyncMock(return_value=[])
        repo.get_team_performance = AsyncMock(return_value=[])
        svc = DashboardService(dashboard_repo=repo)

        resp = await svc.get_management_dashboard(
            role_codes=["admin"],
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 31),
            team_id=None,
            priority_id=None,
            ticket_type=None,
        )

        assert resp.sla.attendance_compliance_pct == 80
        assert resp.sla.resolution_compliance_pct == 60
        assert resp.sla.breached_count == 3
        assert resp.summary.total_tickets == 10
        assert resp.summary.open == 5
        assert resp.summary.closed == 5
