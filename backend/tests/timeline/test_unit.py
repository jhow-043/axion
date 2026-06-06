"""Testes unitários — P10 Timeline.

Cobrem: record_event(), serialização de payload, ordenação cronológica.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.timeline.service import TimelineService


def _make_service(events=None):
    event_repo = AsyncMock()
    ticket_repo = AsyncMock()
    observer_repo = AsyncMock()
    user_repo = AsyncMock()
    if events is not None:
        event_repo.list_for_ticket.return_value = events
        event_repo.count_for_ticket.return_value = len(events)
    svc = TimelineService(
        event_repo=event_repo,
        ticket_repo=ticket_repo,
        observer_repo=observer_repo,
        user_repo=user_repo,
    )
    return svc, event_repo, ticket_repo, observer_repo, user_repo


@pytest.mark.asyncio
async def test_record_event_persists_with_correct_fields():
    svc, event_repo, *_ = _make_service()
    ticket_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    await svc.record_event(
        event_type="ticket_created",
        ticket_id=ticket_id,
        actor_id=actor_id,
    )

    event_repo.create.assert_awaited_once()
    call_data = event_repo.create.call_args[0][0]
    assert call_data["ticket_id"] == ticket_id
    assert call_data["actor_id"] == actor_id
    assert call_data["event_type"] == "ticket_created"
    assert call_data["payload"] is None


@pytest.mark.asyncio
async def test_record_event_persists_payload():
    svc, event_repo, *_ = _make_service()
    payload = {"from_status": "new", "to_status": "in_progress"}

    await svc.record_event(
        event_type="status_changed",
        ticket_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        payload=payload,
    )

    call_data = event_repo.create.call_args[0][0]
    assert call_data["payload"] == payload


@pytest.mark.asyncio
async def test_record_event_allows_null_actor():
    svc, event_repo, *_ = _make_service()

    await svc.record_event(
        event_type="ticket_closed",
        ticket_id=uuid.uuid4(),
        actor_id=None,
        payload={"method": "auto"},
    )

    call_data = event_repo.create.call_args[0][0]
    assert call_data["actor_id"] is None


@pytest.mark.asyncio
async def test_list_events_returns_chronological_order():
    from datetime import UTC, datetime, timedelta

    from app.modules.timeline.models import TicketEvent

    base_time = datetime(2026, 6, 3, 10, 0, 0, tzinfo=UTC)
    events = []
    for i in range(3):
        e = MagicMock(spec=TicketEvent)
        e.id = uuid.uuid4()
        e.event_type = f"event_{i}"
        e.actor_id = None
        e.payload = None
        e.created_at = base_time + timedelta(minutes=i)
        events.append(e)

    svc, event_repo, ticket_repo, observer_repo, user_repo = _make_service(events)
    ticket = MagicMock()
    ticket.id = uuid.uuid4()
    ticket.requester_id = uuid.uuid4()
    ticket.assignee_id = None
    ticket.team_id = None
    ticket_repo.get.return_value = ticket

    result = await svc.list_events(
        ticket.id,
        ticket.requester_id,
        {"requester"},
        page=1,
        page_size=50,
    )

    assert len(result.items) == 3
    for i, item in enumerate(result.items):
        assert item.type == f"event_{i}"


@pytest.mark.asyncio
async def test_list_events_enriches_actor_name():
    from datetime import UTC, datetime

    from app.modules.timeline.models import TicketEvent

    actor_id = uuid.uuid4()
    e = MagicMock(spec=TicketEvent)
    e.id = uuid.uuid4()
    e.event_type = "ticket_created"
    e.actor_id = actor_id
    e.payload = None
    e.created_at = datetime(2026, 6, 3, 10, 0, 0, tzinfo=UTC)

    svc, event_repo, ticket_repo, observer_repo, user_repo = _make_service([e])
    ticket = MagicMock()
    ticket.id = uuid.uuid4()
    ticket.requester_id = uuid.uuid4()
    ticket.assignee_id = None
    ticket.team_id = None
    ticket_repo.get.return_value = ticket

    user = MagicMock()
    user.id = actor_id
    user.name = "João Silva"
    user_repo.get.return_value = user

    result = await svc.list_events(
        ticket.id,
        ticket.requester_id,
        {"requester"},
        page=1,
        page_size=50,
    )

    assert result.items[0].actor is not None
    assert result.items[0].actor.name == "João Silva"


@pytest.mark.asyncio
async def test_list_events_actor_none_shown_as_system():
    from datetime import UTC, datetime

    from app.modules.timeline.models import TicketEvent

    e = MagicMock(spec=TicketEvent)
    e.id = uuid.uuid4()
    e.event_type = "ticket_closed"
    e.actor_id = None
    e.payload = {"method": "auto"}
    e.created_at = datetime(2026, 6, 3, 10, 0, 0, tzinfo=UTC)

    svc, event_repo, ticket_repo, *_ = _make_service([e])
    ticket = MagicMock()
    ticket.id = uuid.uuid4()
    ticket.requester_id = uuid.uuid4()
    ticket.assignee_id = None
    ticket.team_id = None
    ticket_repo.get.return_value = ticket

    result = await svc.list_events(
        ticket.id,
        ticket.requester_id,
        {"requester"},
        page=1,
        page_size=50,
    )

    assert result.items[0].actor is None


@pytest.mark.asyncio
async def test_list_events_raises_not_found_for_unknown_ticket():
    from app.core.exceptions import NotFoundError

    svc, event_repo, ticket_repo, *_ = _make_service([])
    ticket_repo.get.return_value = None

    with pytest.raises(NotFoundError):
        await svc.list_events(uuid.uuid4(), uuid.uuid4(), {"admin"}, page=1, page_size=50)
