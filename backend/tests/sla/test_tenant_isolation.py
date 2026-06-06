"""Tenant isolation tests for P12 SLA — INV-01 + INV-02."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.catalog.models import Priority
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.sla.models import SlaPolicy
from app.modules.sla.repository import SlaPauseRepository, SlaPolicyRepository, SlaTrackerRepository
from app.modules.sla.service import SlaService
from app.modules.tenants.models import Tenant
from app.modules.tickets.repository import TicketRepository
from app.modules.users.seed import seed_default_roles_and_permissions


async def _make_tenant(db: AsyncSession, slug_prefix: str) -> Tenant:
    t = Tenant(name=f"{slug_prefix} Corp", slug=f"{slug_prefix}-{uuid.uuid4().hex[:6]}")
    db.add(t)
    await db.flush()
    await seed_default_roles_and_permissions(db, t.id)
    await seed_catalog_defaults(db, t.id)
    await db.flush()
    return t


async def _get_priority(db: AsyncSession, tenant_id, code="low") -> Priority:
    stmt = select(Priority).where(Priority.tenant_id == tenant_id, Priority.code == code)
    result = await db.execute(stmt)
    return result.scalar_one()


def _make_svc(db: AsyncSession, tenant_id) -> SlaService:
    return SlaService(
        policy_repo=SlaPolicyRepository(db, tenant_id),
        tracker_repo=SlaTrackerRepository(db, tenant_id),
        pause_repo=SlaPauseRepository(db, tenant_id),
        ticket_repo=TicketRepository(db, tenant_id),
    )


@pytest.mark.asyncio
async def test_policy_from_other_tenant_returns_none(db_session: AsyncSession):
    """SlaPolicy created for tenant A is invisible to tenant B's SlaService (INV-01)."""
    tenant_a = await _make_tenant(db_session, "pA")
    tenant_b = await _make_tenant(db_session, "pB")
    prio_a = await _get_priority(db_session, tenant_a.id)

    policy_a = SlaPolicy(
        tenant_id=tenant_a.id,
        ticket_type="predial",
        priority_id=prio_a.id,
        attendance_minutes=60,
        resolution_minutes=480,
        is_active=True,
    )
    db_session.add(policy_a)
    await db_session.flush()

    # Service scoped to tenant B sees nothing
    svc_b = _make_svc(db_session, tenant_b.id)
    prio_b = await _get_priority(db_session, tenant_b.id)
    result = await svc_b._policies.find_applicable(
        ticket_type="predial", priority_id=prio_b.id, team_id=None
    )
    assert result is None


@pytest.mark.asyncio
async def test_tracker_from_other_tenant_invisible(db_session: AsyncSession):
    """SlaTracker created for tenant A cannot be fetched by tenant B's service."""
    tenant_a = await _make_tenant(db_session, "tA")
    tenant_b = await _make_tenant(db_session, "tB")
    prio_a = await _get_priority(db_session, tenant_a.id)

    policy_a = SlaPolicy(
        tenant_id=tenant_a.id,
        ticket_type="predial",
        priority_id=prio_a.id,
        attendance_minutes=60,
        resolution_minutes=480,
        is_active=True,
    )
    db_session.add(policy_a)
    await db_session.flush()

    svc_a = _make_svc(db_session, tenant_a.id)
    ticket_id = uuid.uuid4()
    await svc_a.initialize_tracker(
        ticket_id=ticket_id,
        ticket_type="predial",
        priority_id=prio_a.id,
        team_id=None,
        created_at=datetime.utcnow(),
    )

    # Tenant B cannot see tenant A's tracker
    svc_b = _make_svc(db_session, tenant_b.id)
    tracker = await svc_b._trackers.find_by_ticket(ticket_id)
    assert tracker is None


@pytest.mark.asyncio
async def test_get_ticket_sla_404_for_cross_tenant(db_session: AsyncSession):
    """SlaService.get_ticket_sla() raises NotFoundError for cross-tenant access (INV-02)."""
    tenant_a = await _make_tenant(db_session, "xA")
    tenant_b = await _make_tenant(db_session, "xB")
    prio_a = await _get_priority(db_session, tenant_a.id)

    policy_a = SlaPolicy(
        tenant_id=tenant_a.id,
        ticket_type="predial",
        priority_id=prio_a.id,
        attendance_minutes=60,
        resolution_minutes=480,
        is_active=True,
    )
    db_session.add(policy_a)
    await db_session.flush()

    svc_a = _make_svc(db_session, tenant_a.id)
    ticket_id = uuid.uuid4()
    await svc_a.initialize_tracker(
        ticket_id=ticket_id,
        ticket_type="predial",
        priority_id=prio_a.id,
        team_id=None,
        created_at=datetime.utcnow(),
    )

    # Tenant B's service should not see it → raises NotFoundError (404 behavior, INV-02)
    svc_b = _make_svc(db_session, tenant_b.id)
    with pytest.raises(NotFoundError):
        await svc_b.get_ticket_sla(ticket_id)
