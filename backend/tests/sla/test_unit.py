"""Unit tests for P12 SLA service — no DB, pure business logic."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.sla.service import SlaService, _elapsed_pct

# Use naive datetimes throughout (consistent with SLA module's naive UTC pattern)

# ── _elapsed_pct helper ────────────────────────────────────────────────────────


def test_elapsed_pct_zero_at_start():
    now = datetime(2026, 1, 1, 10, 0)
    due_at = now + timedelta(minutes=60)
    pct = _elapsed_pct(due_at=due_at, total_minutes=60, now=now)
    assert pct == pytest.approx(0.0, abs=1.0)


def test_elapsed_pct_100_at_deadline():
    due_at = datetime(2026, 1, 1, 11, 0)
    now = due_at
    pct = _elapsed_pct(due_at=due_at, total_minutes=60, now=now)
    assert pct == pytest.approx(100.0, abs=1.0)


def test_elapsed_pct_80_at_threshold():
    due_at = datetime(2026, 1, 1, 11, 0)
    now = due_at - timedelta(minutes=12)  # 48 of 60 minutes elapsed → 80%
    pct = _elapsed_pct(due_at=due_at, total_minutes=60, now=now)
    assert pct == pytest.approx(80.0, abs=1.0)


# ── Policy selection order ─────────────────────────────────────────────────────


@pytest.fixture
def svc():
    policy_repo = AsyncMock()
    tracker_repo = AsyncMock()
    pause_repo = AsyncMock()
    ticket_repo = AsyncMock()
    return SlaService(
        policy_repo=policy_repo,
        tracker_repo=tracker_repo,
        pause_repo=pause_repo,
        ticket_repo=ticket_repo,
    )


@pytest.mark.asyncio
async def test_initialize_tracker_no_policy_skips(svc):
    svc._policies.find_applicable = AsyncMock(return_value=None)
    await svc.initialize_tracker(
        ticket_id=uuid4(),
        ticket_type="predial",
        priority_id=uuid4(),
        team_id=None,
        created_at=datetime.utcnow(),
    )
    svc._trackers.create.assert_not_called()


@pytest.mark.asyncio
async def test_initialize_tracker_creates_with_correct_due_at(svc):
    policy = MagicMock()
    policy.id = uuid4()
    policy.attendance_minutes = 60
    svc._policies.find_applicable = AsyncMock(return_value=policy)
    svc._trackers.create = AsyncMock()

    created_at = datetime(2026, 1, 1, 9, 0)  # naive
    await svc.initialize_tracker(
        ticket_id=uuid4(),
        ticket_type="predial",
        priority_id=uuid4(),
        team_id=None,
        created_at=created_at,
    )

    call_kwargs = svc._trackers.create.call_args[0][0]
    expected_due = created_at + timedelta(minutes=60)
    assert call_kwargs["attendance_due_at"] == expected_due
    assert call_kwargs["attendance_status"] == "running"


@pytest.mark.asyncio
async def test_on_ticket_assigned_met(svc):
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.attendance_status = "running"
    tracker.attendance_due_at = datetime(2026, 1, 1, 10, 0)  # naive
    tracker.policy_id = uuid4()

    policy = MagicMock()
    policy.id = tracker.policy_id
    policy.resolution_minutes = 480

    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._policies.get = AsyncMock(return_value=policy)
    svc._trackers.update = AsyncMock()

    assigned_at = datetime(2026, 1, 1, 9, 30)  # before due → met (naive)
    await svc.on_ticket_assigned(ticket_id=uuid4(), assigned_at=assigned_at)

    update_kwargs = svc._trackers.update.call_args[0][1]
    assert update_kwargs["attendance_status"] == "met"
    expected_resolution = assigned_at + timedelta(minutes=480)
    assert update_kwargs["resolution_due_at"] == expected_resolution


@pytest.mark.asyncio
async def test_on_ticket_assigned_breached(svc):
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.attendance_status = "running"
    tracker.attendance_due_at = datetime(2026, 1, 1, 10, 0)  # naive
    tracker.policy_id = uuid4()

    policy = MagicMock()
    policy.resolution_minutes = 120
    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._policies.get = AsyncMock(return_value=policy)
    svc._trackers.update = AsyncMock()

    assigned_at = datetime(2026, 1, 1, 11, 0)  # after due → breached (naive)
    await svc.on_ticket_assigned(ticket_id=uuid4(), assigned_at=assigned_at)

    update_kwargs = svc._trackers.update.call_args[0][1]
    assert update_kwargs["attendance_status"] == "breached"


@pytest.mark.asyncio
async def test_on_ticket_pending_creates_pause(svc):
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.resolution_status = "running"
    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._pauses.create = AsyncMock()
    svc._trackers.update = AsyncMock()

    paused_at = datetime.utcnow()
    await svc.on_ticket_pending(ticket_id=uuid4(), paused_at=paused_at)

    svc._pauses.create.assert_called_once()
    pause_data = svc._pauses.create.call_args[0][0]
    assert pause_data["paused_at"] == paused_at  # naive input stays naive
    svc._trackers.update.assert_called_once()
    assert svc._trackers.update.call_args[0][1]["resolution_status"] == "paused"


@pytest.mark.asyncio
async def test_on_ticket_pending_idempotent_if_already_paused(svc):
    tracker = MagicMock()
    tracker.resolution_status = "paused"  # already paused
    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._pauses.create = AsyncMock()

    await svc.on_ticket_pending(ticket_id=uuid4(), paused_at=datetime.utcnow())
    svc._pauses.create.assert_not_called()


@pytest.mark.asyncio
async def test_on_ticket_resumed_extends_deadline(svc):
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.resolution_status = "paused"
    tracker.total_paused_minutes = 0
    tracker.resolution_due_at = datetime(2026, 1, 1, 17, 0)  # naive

    pause = MagicMock()
    pause.id = uuid4()
    pause.paused_at = datetime(2026, 1, 1, 14, 0)  # naive

    resumed_at = datetime(2026, 1, 1, 15, 0)  # 60 min pause (naive)
    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._pauses.find_open_pause = AsyncMock(return_value=pause)
    svc._pauses.update = AsyncMock()
    svc._trackers.update = AsyncMock()

    await svc.on_ticket_resumed(ticket_id=uuid4(), resumed_at=resumed_at)

    tracker_update = svc._trackers.update.call_args[0][1]
    assert tracker_update["total_paused_minutes"] == 60
    # deadline extended by 60 minutes: 17:00 + 60min = 18:00
    assert tracker_update["resolution_due_at"] == datetime(2026, 1, 1, 18, 0)
    assert tracker_update["resolution_status"] == "running"


@pytest.mark.asyncio
async def test_on_ticket_resolved_met(svc):
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.resolution_status = "running"
    tracker.resolution_due_at = datetime(2026, 1, 1, 17, 0)  # naive
    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._trackers.update = AsyncMock()

    resolved_at = datetime(2026, 1, 1, 16, 0)  # before due (naive)
    await svc.on_ticket_resolved(ticket_id=uuid4(), resolved_at=resolved_at)

    update_data = svc._trackers.update.call_args[0][1]
    assert update_data["resolution_status"] == "met"


@pytest.mark.asyncio
async def test_on_ticket_resolved_breached(svc):
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.resolution_status = "running"
    tracker.resolution_due_at = datetime(2026, 1, 1, 17, 0)  # naive
    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._trackers.update = AsyncMock()

    resolved_at = datetime(2026, 1, 1, 18, 0)  # after due (naive)
    await svc.on_ticket_resolved(ticket_id=uuid4(), resolved_at=resolved_at)

    update_data = svc._trackers.update.call_args[0][1]
    assert update_data["resolution_status"] == "breached"


# ── Sweep idempotency ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sweep_breaches_skips_already_breached(svc):
    # Tracker already breached → no DB write
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.attendance_status = "breached"
    tracker.resolution_status = "breached"
    svc._trackers.list_overdue = AsyncMock(return_value=[tracker])
    svc._trackers.update = AsyncMock()

    await svc.sweep_breaches()
    svc._trackers.update.assert_not_called()


@pytest.mark.asyncio
async def test_sweep_alerts_does_not_double_alert(svc):
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.ticket_id = uuid4()
    tracker.policy_id = uuid4()
    tracker.attendance_status = "running"
    tracker.attendance_alert_sent = True  # already sent
    tracker.attendance_due_at = datetime(2026, 1, 1, 10, 0)
    tracker.resolution_status = "met"
    tracker.resolution_alert_sent = True
    tracker.resolution_due_at = None
    tracker.total_paused_minutes = 0

    policy = MagicMock()
    policy.attendance_minutes = 60
    policy.resolution_minutes = 480
    policy.alert_threshold_pct = 80
    svc._trackers.list_running = AsyncMock(return_value=[tracker])
    svc._policies.get = AsyncMock(return_value=policy)
    svc._trackers.update = AsyncMock()

    await svc.sweep_alerts()
    svc._trackers.update.assert_not_called()
