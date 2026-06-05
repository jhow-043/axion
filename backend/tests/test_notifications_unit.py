"""Unit tests for P14 — Notificações.

Tests business rules that do not require DB access:
  - Title / body generation
  - Recipient strategy mapping
  - Actor exclusion from recipients
  - Preferences respected for email
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.modules.notifications.service import (
    _RECIPIENT_STRATEGY,
    _TITLE_MAP,
    NotificationService,
    _build_body,
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
