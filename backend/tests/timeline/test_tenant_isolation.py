"""Testes de isolamento de tenant — P10 Timeline.

Garante que eventos de um tenant não vazam para outro.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.locations.models import Location
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.timeline.repository import TicketEventRepository


async def _create_tenant_with_ticket(db_session: AsyncSession, suffix: str):
    from app.core.security import hash_password
    from app.modules.catalog.models import Priority, Status
    from app.modules.catalog.seed import seed_catalog_defaults
    from app.modules.users.models import User

    tenant = Tenant(name=f"Tenant {suffix}", slug=f"iso-tl-{suffix}-{uuid.uuid4().hex[:6]}")
    db_session.add(tenant)
    await db_session.flush()

    await seed_catalog_defaults(db_session, tenant.id)
    await db_session.flush()

    from sqlalchemy import select

    priority = (
        await db_session.execute(
            select(Priority).where(Priority.tenant_id == tenant.id, Priority.code == "low")
        )
    ).scalar_one()
    status = (
        await db_session.execute(
            select(Status).where(Status.tenant_id == tenant.id, Status.code == "new")
        )
    ).scalar_one()

    user = User(
        tenant_id=tenant.id,
        name=f"User {suffix}",
        email=f"user-{suffix}@iso.test",
        password_hash=hash_password("test"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    loc = Location(tenant_id=tenant.id, name="Loc", is_active=True)
    db_session.add(loc)
    await db_session.flush()

    ticket = Ticket(
        tenant_id=tenant.id,
        type="predial",
        title="Isolation ticket",
        description="desc",
        priority_id=priority.id,
        status_id=status.id,
        location_id=loc.id,
        requester_id=user.id,
    )
    db_session.add(ticket)
    await db_session.flush()

    return tenant, ticket, user


@pytest.mark.asyncio
async def test_events_scoped_to_tenant(db_session: AsyncSession):
    tenant_a, ticket_a, user_a = await _create_tenant_with_ticket(db_session, "a")
    tenant_b, ticket_b, user_b = await _create_tenant_with_ticket(db_session, "b")

    repo_a = TicketEventRepository(db_session, tenant_a.id)
    repo_b = TicketEventRepository(db_session, tenant_b.id)

    await repo_a.create(
        {
            "ticket_id": ticket_a.id,
            "actor_id": user_a.id,
            "event_type": "ticket_created",
            "payload": None,
        }
    )
    await repo_b.create(
        {
            "ticket_id": ticket_b.id,
            "actor_id": user_b.id,
            "event_type": "ticket_created",
            "payload": None,
        }
    )

    # tenant_a's repo must not see tenant_b's events
    events_a = await repo_a.list_for_ticket(ticket_a.id)
    assert all(e.tenant_id == tenant_a.id for e in events_a)

    events_b = await repo_b.list_for_ticket(ticket_b.id)
    assert all(e.tenant_id == tenant_b.id for e in events_b)


@pytest.mark.asyncio
async def test_cross_tenant_ticket_timeline_returns_empty(db_session: AsyncSession):
    """Tenant A's repo cannot see Tenant B's ticket events (returns empty list, not error)."""
    tenant_a, ticket_a, user_a = await _create_tenant_with_ticket(db_session, "x")
    tenant_b, ticket_b, user_b = await _create_tenant_with_ticket(db_session, "y")

    repo_b = TicketEventRepository(db_session, tenant_b.id)
    await repo_b.create(
        {
            "ticket_id": ticket_b.id,
            "actor_id": user_b.id,
            "event_type": "ticket_created",
            "payload": None,
        }
    )

    # Tenant A's repo tries to access tenant B's ticket — must return empty
    repo_a = TicketEventRepository(db_session, tenant_a.id)
    events = await repo_a.list_for_ticket(ticket_b.id)
    assert events == []
