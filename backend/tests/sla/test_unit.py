"""Unit tests for P12 SLA service — no DB, pure business logic."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.modules.sla.schemas import SlaPolicyPatch
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


# ── Policy NotFound paths ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_policy_raises_not_found(svc):
    svc._policies.get = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await svc.get_policy(uuid4())


@pytest.mark.asyncio
async def test_update_policy_raises_not_found(svc):
    svc._policies.get = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await svc.update_policy(uuid4(), SlaPolicyPatch())


@pytest.mark.asyncio
async def test_deactivate_policy_raises_not_found(svc):
    svc._policies.get = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await svc.deactivate_policy(uuid4())


# ── on_ticket_assigned: policy missing ────────────────────────────────────────


@pytest.mark.asyncio
async def test_on_ticket_assigned_noop_when_policy_missing(svc):
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.attendance_status = "running"
    tracker.attendance_due_at = datetime(2026, 1, 1, 10, 0)
    tracker.policy_id = uuid4()
    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._policies.get = AsyncMock(return_value=None)
    svc._trackers.update = AsyncMock()

    await svc.on_ticket_assigned(ticket_id=uuid4(), assigned_at=datetime(2026, 1, 1, 9, 0))
    svc._trackers.update.assert_not_called()


# ── on_ticket_resumed: no open pause ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_on_ticket_resumed_noop_when_no_open_pause(svc):
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.resolution_status = "paused"
    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._pauses.find_open_pause = AsyncMock(return_value=None)
    svc._trackers.update = AsyncMock()

    await svc.on_ticket_resumed(ticket_id=uuid4(), resumed_at=datetime.utcnow())
    svc._trackers.update.assert_not_called()


# ── get_ticket_sla: running tracker with elapsed calculation ──────────────────


@pytest.mark.asyncio
async def test_get_ticket_sla_running_calculates_elapsed_and_remaining(svc):
    now = datetime.utcnow()
    tracker = MagicMock()
    tracker.policy_id = uuid4()
    tracker.attendance_status = "met"
    tracker.attendance_due_at = now - timedelta(hours=2)
    tracker.attendance_met_at = now - timedelta(hours=3)
    tracker.resolution_status = "running"
    tracker.resolution_due_at = now + timedelta(hours=2)
    tracker.resolution_met_at = None
    tracker.total_paused_minutes = 30

    policy = MagicMock()
    policy.resolution_minutes = 480

    svc._trackers.find_by_ticket = AsyncMock(return_value=tracker)
    svc._policies.get = AsyncMock(return_value=policy)

    result = await svc.get_ticket_sla(uuid4())

    assert result.resolution.remaining_minutes is not None
    assert result.resolution.elapsed_minutes is not None
    assert result.resolution.remaining_minutes >= 0
    assert result.resolution.elapsed_minutes >= 0


# ── sweep_breaches: timeline + notification calls ─────────────────────────────


@pytest.mark.asyncio
async def test_sweep_breaches_records_timeline_and_notifies():
    past = datetime(2024, 1, 1, 10, 0)  # clearly in the past
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.ticket_id = uuid4()
    tracker.attendance_status = "running"
    tracker.attendance_due_at = past
    tracker.resolution_status = "running"
    tracker.resolution_due_at = past

    timeline_svc = AsyncMock()
    notification_svc = AsyncMock()
    tracker_repo = AsyncMock()
    tracker_repo.list_overdue = AsyncMock(return_value=[tracker])
    tracker_repo.update = AsyncMock()

    svc = SlaService(
        policy_repo=AsyncMock(),
        tracker_repo=tracker_repo,
        pause_repo=AsyncMock(),
        ticket_repo=AsyncMock(),
        timeline_svc=timeline_svc,
        notification_svc=notification_svc,
    )

    await svc.sweep_breaches()

    tracker_repo.update.assert_awaited_once()
    timeline_svc.record_event.assert_awaited()
    notification_svc.notify.assert_awaited()


@pytest.mark.asyncio
async def test_sweep_breaches_breach_resolution_only():
    """Only resolution breached (attendance already met)."""
    past = datetime(2024, 1, 1, 10, 0)
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.ticket_id = uuid4()
    tracker.attendance_status = "met"   # not running → skip attendance check
    tracker.attendance_due_at = past
    tracker.resolution_status = "running"
    tracker.resolution_due_at = past

    tracker_repo = AsyncMock()
    tracker_repo.list_overdue = AsyncMock(return_value=[tracker])
    tracker_repo.update = AsyncMock()
    notification_svc = AsyncMock()

    svc = SlaService(
        policy_repo=AsyncMock(),
        tracker_repo=tracker_repo,
        pause_repo=AsyncMock(),
        ticket_repo=AsyncMock(),
        notification_svc=notification_svc,
    )

    await svc.sweep_breaches()
    update_data = tracker_repo.update.call_args[0][1]
    assert "resolution_status" in update_data
    assert "attendance_status" not in update_data


# ── sweep_alerts: policy None skips, attendance + resolution alerts ───────────


@pytest.mark.asyncio
async def test_sweep_alerts_skips_tracker_when_policy_none(svc):
    tracker = MagicMock()
    tracker.policy_id = uuid4()
    svc._trackers.list_running = AsyncMock(return_value=[tracker])
    svc._policies.get = AsyncMock(return_value=None)
    svc._trackers.update = AsyncMock()

    await svc.sweep_alerts()
    svc._trackers.update.assert_not_called()


@pytest.mark.asyncio
async def test_sweep_alerts_sends_attendance_alert():
    now = datetime.utcnow()
    # 55 of 60 minutes elapsed → pct ≈ 91.6% > 80% threshold
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.ticket_id = uuid4()
    tracker.policy_id = uuid4()
    tracker.attendance_status = "running"
    tracker.attendance_alert_sent = False
    tracker.attendance_due_at = now + timedelta(minutes=5)
    tracker.resolution_status = "met"
    tracker.resolution_alert_sent = True
    tracker.resolution_due_at = None
    tracker.total_paused_minutes = 0

    policy = MagicMock()
    policy.attendance_minutes = 60
    policy.resolution_minutes = 480
    policy.alert_threshold_pct = 80

    notification_svc = AsyncMock()
    tracker_repo = AsyncMock()
    tracker_repo.list_running = AsyncMock(return_value=[tracker])
    tracker_repo.update = AsyncMock()
    policy_repo = AsyncMock()
    policy_repo.get = AsyncMock(return_value=policy)

    svc = SlaService(
        policy_repo=policy_repo,
        tracker_repo=tracker_repo,
        pause_repo=AsyncMock(),
        ticket_repo=AsyncMock(),
        notification_svc=notification_svc,
    )

    await svc.sweep_alerts()

    notification_svc.notify.assert_awaited_once()
    call_kwargs = notification_svc.notify.call_args.kwargs
    assert call_kwargs["event_type"] == "sla_attendance_alert"
    tracker_repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_sweep_alerts_sends_resolution_alert():
    now = datetime.utcnow()
    tracker = MagicMock()
    tracker.id = uuid4()
    tracker.ticket_id = uuid4()
    tracker.policy_id = uuid4()
    tracker.attendance_status = "met"
    tracker.attendance_alert_sent = True
    tracker.attendance_due_at = now - timedelta(hours=1)
    tracker.resolution_status = "running"
    tracker.resolution_alert_sent = False
    tracker.resolution_due_at = now + timedelta(minutes=5)
    tracker.total_paused_minutes = 0

    policy = MagicMock()
    policy.attendance_minutes = 60
    policy.resolution_minutes = 60
    policy.alert_threshold_pct = 80

    notification_svc = AsyncMock()
    tracker_repo = AsyncMock()
    tracker_repo.list_running = AsyncMock(return_value=[tracker])
    tracker_repo.update = AsyncMock()
    policy_repo = AsyncMock()
    policy_repo.get = AsyncMock(return_value=policy)

    svc = SlaService(
        policy_repo=policy_repo,
        tracker_repo=tracker_repo,
        pause_repo=AsyncMock(),
        ticket_repo=AsyncMock(),
        notification_svc=notification_svc,
    )

    await svc.sweep_alerts()

    notification_svc.notify.assert_awaited_once()
    call_kwargs = notification_svc.notify.call_args.kwargs
    assert call_kwargs["event_type"] == "sla_resolution_alert"
    tracker_repo.update.assert_awaited_once()
