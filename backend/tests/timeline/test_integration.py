"""Testes de integração — P10 Timeline.

Cobrem: persistência de eventos, GET /timeline, controle de acesso.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.timeline.models import TicketEvent
from app.modules.timeline.repository import TicketEventRepository
from app.modules.users.models import User


@pytest.mark.asyncio
async def test_record_event_persists_ticket_created(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    requester_user: User,
):
    repo = TicketEventRepository(db_session, seeded_tenant.id)
    event = await repo.create(
        {
            "ticket_id": sample_ticket.id,
            "actor_id": requester_user.id,
            "event_type": "ticket_created",
            "payload": None,
        }
    )
    assert event.id is not None
    assert event.event_type == "ticket_created"
    assert event.actor_id == requester_user.id
    assert event.payload is None


@pytest.mark.asyncio
async def test_record_event_persists_payload(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    admin_user: User,
):
    repo = TicketEventRepository(db_session, seeded_tenant.id)
    payload = {"from_status": "new", "to_status": "in_progress"}
    event = await repo.create(
        {
            "ticket_id": sample_ticket.id,
            "actor_id": admin_user.id,
            "event_type": "status_changed",
            "payload": payload,
        }
    )
    assert event.payload == payload


@pytest.mark.asyncio
async def test_list_for_ticket_returns_chronological_order(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    admin_user: User,
):
    repo = TicketEventRepository(db_session, seeded_tenant.id)
    for etype in ("ticket_created", "status_changed", "comment_added"):
        await repo.create(
            {
                "ticket_id": sample_ticket.id,
                "actor_id": admin_user.id,
                "event_type": etype,
                "payload": None,
            }
        )

    events = await repo.list_for_ticket(sample_ticket.id)
    assert len(events) == 3
    # verify ascending order
    for i in range(len(events) - 1):
        assert events[i].created_at <= events[i + 1].created_at


@pytest.mark.asyncio
async def test_count_for_ticket(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    admin_user: User,
):
    repo = TicketEventRepository(db_session, seeded_tenant.id)
    for _ in range(4):
        await repo.create(
            {
                "ticket_id": sample_ticket.id,
                "actor_id": admin_user.id,
                "event_type": "ticket_created",
                "payload": None,
            }
        )
    total = await repo.count_for_ticket(sample_ticket.id)
    assert total == 4


@pytest.mark.asyncio
async def test_get_timeline_api_returns_events(
    admin_client,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    admin_user: User,
):
    repo = TicketEventRepository(db_session, seeded_tenant.id)
    await repo.create(
        {
            "ticket_id": sample_ticket.id,
            "actor_id": admin_user.id,
            "event_type": "ticket_created",
            "payload": None,
        }
    )

    resp = await admin_client.get(f"/api/v1/tickets/{sample_ticket.id}/timeline")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert body["page"] == 1
    assert "items" in body


@pytest.mark.asyncio
async def test_get_timeline_api_chronological(
    admin_client,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sample_ticket: Ticket,
    admin_user: User,
):
    repo = TicketEventRepository(db_session, seeded_tenant.id)
    for etype in ("ticket_created", "comment_added", "status_changed"):
        await repo.create(
            {
                "ticket_id": sample_ticket.id,
                "actor_id": admin_user.id,
                "event_type": etype,
                "payload": None,
            }
        )

    resp = await admin_client.get(f"/api/v1/tickets/{sample_ticket.id}/timeline")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) >= 3
    # verify ascending order
    times = [i["created_at"] for i in items]
    assert times == sorted(times)


@pytest.mark.asyncio
async def test_get_timeline_requires_auth(anon_client, sample_ticket: Ticket):
    resp = await anon_client.get(f"/api/v1/tickets/{sample_ticket.id}/timeline")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_timeline_non_participant_gets_404(
    requester_client,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    default_priority,
    default_status_new,
    active_location,
):
    """Requester que não é dono do ticket recebe 404 (INV-02)."""
    other_ticket = Ticket(
        tenant_id=seeded_tenant.id,
        type="predial",
        title="Outro ticket",
        description="desc",
        priority_id=default_priority.id,
        status_id=default_status_new.id,
        location_id=active_location.id,
        requester_id=admin_user.id,  # owned by admin, not by requester_client user
    )
    db_session.add(other_ticket)
    await db_session.flush()

    resp = await requester_client.get(f"/api/v1/tickets/{other_ticket.id}/timeline")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_timeline_no_edit_or_delete_endpoints(admin_client, sample_ticket: Ticket):
    """Spec: nenhum endpoint de edição ou exclusão de eventos está exposto."""
    ticket_id = sample_ticket.id
    fake_event_id = "00000000-0000-0000-0000-000000000001"

    delete_resp = await admin_client.delete(
        f"/api/v1/tickets/{ticket_id}/timeline/{fake_event_id}"
    )
    assert delete_resp.status_code == 404

    patch_resp = await admin_client.patch(
        f"/api/v1/tickets/{ticket_id}/timeline/{fake_event_id}",
        json={"event_type": "hacked"},
    )
    assert patch_resp.status_code in (404, 405)
