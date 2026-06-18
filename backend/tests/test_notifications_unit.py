"""Unit tests for P14 — Notificações.

Tests business rules that do not require DB access:
  - Title / body generation
  - Recipient strategy mapping
  - Actor exclusion from recipients
  - Preferences respected for email
"""

from __future__ import annotations

import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.notifications.service import (
    _RECIPIENT_STRATEGY,
    _TITLE_MAP,
    NotificationService,
    _build_body,
)

# ── helpers ───────────────────────────────────────────────────────────────────


def _make_notif(ticket_id=None):
    n = MagicMock()
    n.id = uuid4()
    n.ticket_id = ticket_id or uuid4()
    n.event_type = "test"
    n.title = "t"
    n.body = "b"
    n.created_at = None
    n.is_read = False
    n.read_at = None
    return n


def _make_svc(ticket=None, extra_notif_repo=None):
    """Build a fully-wired NotificationService with all repos mocked."""
    notif_repo = extra_notif_repo or AsyncMock()
    notif_repo.create = AsyncMock(return_value=_make_notif())
    pref_repo = AsyncMock()
    pref_repo.find = AsyncMock(return_value=None)
    ticket_repo = AsyncMock()
    ticket_repo.get = AsyncMock(return_value=ticket)
    recipient_repo = AsyncMock()
    recipient_repo.get_observer_user_ids = AsyncMock(return_value=[])
    recipient_repo.get_users_by_role_codes = AsyncMock(return_value=[])
    recipient_repo.get_team_users_by_role_codes = AsyncMock(return_value=[])
    recipient_repo.get_user_email = AsyncMock(return_value=None)
    return NotificationService(
        notification_repo=notif_repo,
        preference_repo=pref_repo,
        ticket_repo=ticket_repo,
        recipient_repo=recipient_repo,
        redis_url=None,
    )

# ── _build_body helper ────────────────────────────────────────────────────────


def test_build_body_known_event():
    ticket = MagicMock()
    ticket.title = "Elevador parado"
    body = _build_body("ticket_created", ticket)
    assert "Elevador parado" in body


def test_build_body_unknown_event():
    ticket = MagicMock()
    ticket.title = "X"
    body = _build_body("unknown_event", ticket)
    assert "unknown_event" in body


def test_build_body_no_ticket():
    body = _build_body("ticket_assigned", None)
    assert isinstance(body, str)
    assert len(body) > 0


# ── Title map completeness ────────────────────────────────────────────────────


def test_title_map_covers_all_strategies():
    """Every event in _RECIPIENT_STRATEGY has a human-readable title."""
    for event in _RECIPIENT_STRATEGY:
        assert event in _TITLE_MAP, f"Missing title for event: {event}"


# ── Stub mode (no-op) ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_stub_mode_is_noop():
    """NotificationService() with no repos must silently do nothing."""
    svc = NotificationService()
    # Should not raise
    await svc.notify(
        event_type="ticket_created",
        ticket_id=uuid4(),
        actor_id=uuid4(),
    )


# ── Actor exclusion ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_excludes_actor():
    """RN-07: the actor of an action must not receive their own notification."""
    actor_id = uuid4()
    requester_id = actor_id  # actor IS the requester
    ticket_id = uuid4()

    ticket = MagicMock()
    ticket.id = ticket_id
    ticket.requester_id = requester_id
    ticket.assignee_id = None
    ticket.team_id = None

    notif_repo = AsyncMock()
    notif_repo.find = AsyncMock(return_value=None)
    notif_repo.create = AsyncMock(
        return_value=MagicMock(
            id=uuid4(),
            is_read=False,
            is_read_at=None,
            ticket_id=ticket_id,
            event_type="ticket_assigned",
            title="t",
            body="b",
            created_at=None,
            read_at=None,
        )
    )

    pref_repo = AsyncMock()
    pref_repo.find = AsyncMock(return_value=None)

    ticket_repo = AsyncMock()
    ticket_repo.get = AsyncMock(return_value=ticket)

    recipient_repo = AsyncMock()
    recipient_repo.get_observer_user_ids = AsyncMock(return_value=[])
    recipient_repo.get_users_by_role_codes = AsyncMock(return_value=[])
    recipient_repo.get_team_users_by_role_codes = AsyncMock(return_value=[])

    svc = NotificationService(
        notification_repo=notif_repo,
        preference_repo=pref_repo,
        ticket_repo=ticket_repo,
        recipient_repo=recipient_repo,
        redis_url=None,
    )

    # ticket_assigned → recipients = requester + observers
    # requester IS the actor → after exclusion, recipients is empty → no persistence
    await svc.notify(
        event_type="ticket_assigned",
        ticket_id=ticket_id,
        actor_id=actor_id,
    )

    notif_repo.create.assert_not_called()


# ── Preferences: email opt-out ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_respects_email_optout():
    """RN-02: when email_enabled=False, no email task is enqueued."""
    recipient_id = uuid4()
    ticket_id = uuid4()

    pref = MagicMock()
    pref.in_app_enabled = True
    pref.email_enabled = False

    ticket = MagicMock()
    ticket.requester_id = recipient_id
    ticket.assignee_id = None
    ticket.team_id = None

    created_notif = MagicMock()
    created_notif.id = uuid4()
    created_notif.ticket_id = ticket_id
    created_notif.event_type = "ticket_assigned"
    created_notif.title = "t"
    created_notif.body = "b"
    created_notif.created_at = None
    created_notif.is_read = False
    created_notif.read_at = None

    notif_repo = AsyncMock()
    notif_repo.create = AsyncMock(return_value=created_notif)

    pref_repo = AsyncMock()
    pref_repo.find = AsyncMock(return_value=pref)

    ticket_repo = AsyncMock()
    ticket_repo.get = AsyncMock(return_value=ticket)

    recipient_repo = AsyncMock()
    recipient_repo.get_observer_user_ids = AsyncMock(return_value=[])
    recipient_repo.get_users_by_role_codes = AsyncMock(return_value=[])
    recipient_repo.get_team_users_by_role_codes = AsyncMock(return_value=[])
    recipient_repo.get_user_email = AsyncMock(return_value="user@test.com")

    svc = NotificationService(
        notification_repo=notif_repo,
        preference_repo=pref_repo,
        ticket_repo=ticket_repo,
        recipient_repo=recipient_repo,
        redis_url=None,
    )

    # Patch Celery send_task to detect if email was enqueued
    import unittest.mock as mock

    with mock.patch("celery.current_app.send_task") as mock_send_task:
        await svc.notify(
            event_type="ticket_assigned",
            ticket_id=ticket_id,
            actor_id=uuid4(),  # different actor
        )
        mock_send_task.assert_not_called()

    # In-app notification must still be persisted (RN-01)
    notif_repo.create.assert_called_once()


# ── Preferences: in-app opt-out ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_respects_inapp_optout():
    """When in_app_enabled=False, notification is NOT persisted."""
    recipient_id = uuid4()
    ticket_id = uuid4()

    pref = MagicMock()
    pref.in_app_enabled = False
    pref.email_enabled = False

    ticket = MagicMock()
    ticket.requester_id = recipient_id
    ticket.assignee_id = None
    ticket.team_id = None

    notif_repo = AsyncMock()
    pref_repo = AsyncMock()
    pref_repo.find = AsyncMock(return_value=pref)

    ticket_repo = AsyncMock()
    ticket_repo.get = AsyncMock(return_value=ticket)

    recipient_repo = AsyncMock()
    recipient_repo.get_observer_user_ids = AsyncMock(return_value=[])
    recipient_repo.get_users_by_role_codes = AsyncMock(return_value=[])
    recipient_repo.get_team_users_by_role_codes = AsyncMock(return_value=[])

    svc = NotificationService(
        notification_repo=notif_repo,
        preference_repo=pref_repo,
        ticket_repo=ticket_repo,
        recipient_repo=recipient_repo,
        redis_url=None,
    )

    await svc.notify(
        event_type="ticket_assigned",
        ticket_id=ticket_id,
        actor_id=uuid4(),
    )

    notif_repo.create.assert_not_called()


# ── extra_recipients ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_extra_recipients():
    """extra_recipients are included regardless of event strategy."""
    extra_id = uuid4()
    ticket_id = uuid4()

    ticket = MagicMock()
    ticket.requester_id = uuid4()
    ticket.assignee_id = None
    ticket.team_id = None

    created_notif = MagicMock()
    created_notif.id = uuid4()
    created_notif.ticket_id = ticket_id
    created_notif.event_type = "ticket_created"
    created_notif.title = "t"
    created_notif.body = "b"
    created_notif.created_at = None
    created_notif.is_read = False
    created_notif.read_at = None

    notif_repo = AsyncMock()
    notif_repo.create = AsyncMock(return_value=created_notif)

    pref_repo = AsyncMock()
    pref_repo.find = AsyncMock(return_value=None)

    ticket_repo = AsyncMock()
    ticket_repo.get = AsyncMock(return_value=ticket)

    recipient_repo = AsyncMock()
    recipient_repo.get_observer_user_ids = AsyncMock(return_value=[])
    recipient_repo.get_users_by_role_codes = AsyncMock(return_value=[])
    recipient_repo.get_team_users_by_role_codes = AsyncMock(return_value=[])
    recipient_repo.get_user_email = AsyncMock(return_value=None)

    svc = NotificationService(
        notification_repo=notif_repo,
        preference_repo=pref_repo,
        ticket_repo=ticket_repo,
        recipient_repo=recipient_repo,
        redis_url=None,
    )

    await svc.notify(
        event_type="ticket_created",
        ticket_id=ticket_id,
        actor_id=uuid4(),
        extra_recipients=[extra_id],
    )

    # extra_id should have received a notification (among others)
    all_calls = notif_repo.create.call_args_list
    recipient_ids = {call.args[0]["recipient_id"] for call in all_calls}
    assert extra_id in recipient_ids


# ── Strategy: requester_assignee_observers ────────────────────────────────────


@pytest.mark.asyncio
async def test_strategy_requester_assignee_observers():
    """ticket_status_changed → requester + assignee + observers all notified."""
    requester_id = uuid4()
    assignee_id = uuid4()
    actor_id = uuid4()
    ticket_id = uuid4()

    ticket = MagicMock()
    ticket.requester_id = requester_id
    ticket.assignee_id = assignee_id
    ticket.team_id = None

    svc = _make_svc(ticket=ticket)
    await svc.notify(
        event_type="ticket_status_changed",
        ticket_id=ticket_id,
        actor_id=actor_id,
    )

    all_calls = svc._notifications.create.call_args_list
    recipient_ids = {c.args[0]["recipient_id"] for c in all_calls}
    assert requester_id in recipient_ids
    assert assignee_id in recipient_ids


# ── Strategy: requester ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_strategy_requester_only():
    """ticket_validation_requested → only the requester is notified."""
    requester_id = uuid4()
    actor_id = uuid4()
    ticket_id = uuid4()

    ticket = MagicMock()
    ticket.requester_id = requester_id
    ticket.assignee_id = uuid4()
    ticket.team_id = None

    svc = _make_svc(ticket=ticket)
    await svc.notify(
        event_type="ticket_validation_requested",
        ticket_id=ticket_id,
        actor_id=actor_id,
    )

    all_calls = svc._notifications.create.call_args_list
    recipient_ids = {c.args[0]["recipient_id"] for c in all_calls}
    assert requester_id in recipient_ids
    assert ticket.assignee_id not in recipient_ids


# ── Strategy: assignee_and_observers ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_strategy_assignee_and_observers():
    """ticket_validation_approved → assignee + observers notified."""
    assignee_id = uuid4()
    observer_id = uuid4()
    actor_id = uuid4()
    ticket_id = uuid4()

    ticket = MagicMock()
    ticket.requester_id = uuid4()
    ticket.assignee_id = assignee_id
    ticket.team_id = None

    svc = _make_svc(ticket=ticket)
    svc._recipients.get_observer_user_ids = AsyncMock(return_value=[observer_id])

    await svc.notify(
        event_type="ticket_validation_approved",
        ticket_id=ticket_id,
        actor_id=actor_id,
    )

    all_calls = svc._notifications.create.call_args_list
    recipient_ids = {c.args[0]["recipient_id"] for c in all_calls}
    assert assignee_id in recipient_ids
    assert observer_id in recipient_ids


# ── Strategy: all_participants_and_team_supervisors ───────────────────────────


@pytest.mark.asyncio
async def test_strategy_all_participants_and_team_supervisors():
    """ticket_auto_closed → requester + assignee + observers + supervisors."""
    requester_id = uuid4()
    assignee_id = uuid4()
    supervisor_id = uuid4()
    actor_id = uuid4()
    ticket_id = uuid4()

    ticket = MagicMock()
    ticket.requester_id = requester_id
    ticket.assignee_id = assignee_id
    ticket.team_id = None

    svc = _make_svc(ticket=ticket)
    svc._recipients.get_users_by_role_codes = AsyncMock(return_value=[supervisor_id])

    await svc.notify(
        event_type="ticket_auto_closed",
        ticket_id=ticket_id,
        actor_id=actor_id,
    )

    all_calls = svc._notifications.create.call_args_list
    recipient_ids = {c.args[0]["recipient_id"] for c in all_calls}
    assert requester_id in recipient_ids
    assert assignee_id in recipient_ids
    assert supervisor_id in recipient_ids


# ── Strategy: assignee_and_team_supervisors ───────────────────────────────────


@pytest.mark.asyncio
async def test_strategy_assignee_and_team_supervisors():
    """sla_attendance_breached → assignee + supervisors, NOT requester."""
    assignee_id = uuid4()
    supervisor_id = uuid4()
    actor_id = uuid4()
    ticket_id = uuid4()

    ticket = MagicMock()
    ticket.requester_id = uuid4()
    ticket.assignee_id = assignee_id
    ticket.team_id = None

    svc = _make_svc(ticket=ticket)
    svc._recipients.get_users_by_role_codes = AsyncMock(return_value=[supervisor_id])

    await svc.notify(
        event_type="sla_attendance_breached",
        ticket_id=ticket_id,
        actor_id=actor_id,
    )

    all_calls = svc._notifications.create.call_args_list
    recipient_ids = {c.args[0]["recipient_id"] for c in all_calls}
    assert assignee_id in recipient_ids
    assert supervisor_id in recipient_ids
    assert ticket.requester_id not in recipient_ids


# ── Strategy: team supervisors with team_id → get_team_users_by_role_codes ───


@pytest.mark.asyncio
async def test_strategy_team_supervisors_with_team_id():
    """ticket_created with team_id → get_team_users_by_role_codes (not global)."""
    team_id = uuid4()
    team_supervisor_id = uuid4()
    ticket_id = uuid4()

    ticket = MagicMock()
    ticket.requester_id = uuid4()
    ticket.assignee_id = None
    ticket.team_id = team_id

    svc = _make_svc(ticket=ticket)
    svc._recipients.get_team_users_by_role_codes = AsyncMock(return_value=[team_supervisor_id])

    await svc.notify(
        event_type="ticket_created",
        ticket_id=ticket_id,
        actor_id=uuid4(),
    )

    svc._recipients.get_team_users_by_role_codes.assert_awaited_once()
    svc._recipients.get_users_by_role_codes.assert_not_awaited()
    all_calls = svc._notifications.create.call_args_list
    recipient_ids = {c.args[0]["recipient_id"] for c in all_calls}
    assert team_supervisor_id in recipient_ids


# ── _enqueue_email guard: _recipients is None + ticket is None ────────────────


@pytest.mark.asyncio
async def test_enqueue_email_noop_when_recipient_repo_none():
    """_enqueue_email returns early when _recipients is None (lines 238-239).
    Also exercises line 257: _resolve_recipients returns empty when ticket is None.
    extra_recipients bypass the strategy so _dispatch (and _enqueue_email) is still called."""
    extra_id = uuid4()
    ticket_id = uuid4()

    notif_repo = AsyncMock()
    notif_repo.create = AsyncMock(return_value=_make_notif(ticket_id))
    pref_repo = AsyncMock()
    pref_repo.find = AsyncMock(return_value=None)

    svc = NotificationService(
        notification_repo=notif_repo,
        preference_repo=pref_repo,
        ticket_repo=None,      # ticket will be None → hits line 257
        recipient_repo=None,   # _recipients is None → hits line 239
        redis_url=None,
    )

    with mock.patch("celery.current_app.send_task") as mock_send:
        await svc.notify(
            event_type="ticket_assigned",
            ticket_id=ticket_id,
            actor_id=uuid4(),
            extra_recipients=[extra_id],
        )
        mock_send.assert_not_called()

    notif_repo.create.assert_called_once()
