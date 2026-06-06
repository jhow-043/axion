"""Integration tests for P12 SLA — rotas + banco."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Priority
from app.modules.sla.models import SlaPolicy, SlaTracker
from app.modules.sla.repository import SlaPauseRepository, SlaPolicyRepository, SlaTrackerRepository
from app.modules.sla.service import SlaService
from app.modules.tenants.models import Tenant
from app.modules.tickets.repository import TicketRepository

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_svc(db: AsyncSession, tenant_id) -> SlaService:
    return SlaService(
        policy_repo=SlaPolicyRepository(db, tenant_id),
        tracker_repo=SlaTrackerRepository(db, tenant_id),
        pause_repo=SlaPauseRepository(db, tenant_id),
        ticket_repo=TicketRepository(db, tenant_id),
    )


async def _get_tracker(db: AsyncSession, ticket_id, tenant_id) -> SlaTracker | None:
    stmt = select(SlaTracker).where(
        SlaTracker.ticket_id == ticket_id, SlaTracker.tenant_id == tenant_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ── Policy API ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_policy(
    admin_client: AsyncClient, default_priority: Priority, seeded_tenant: Tenant
):
    resp = await admin_client.post(
        "/api/v1/sla/policies",
        json={
            "ticket_type": "predial",
            "priority_id": str(default_priority.id),
            "attendance_minutes": 60,
            "resolution_minutes": 480,
            "alert_threshold_pct": 80,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["ticket_type"] == "predial"
    assert data["attendance_minutes"] == 60
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_policies(admin_client: AsyncClient, sla_policy: SlaPolicy):
    resp = await admin_client.get("/api/v1/sla/policies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    ids = [p["id"] for p in data["items"]]
    assert str(sla_policy.id) in ids


@pytest.mark.asyncio
async def test_get_policy(admin_client: AsyncClient, sla_policy: SlaPolicy):
    resp = await admin_client.get(f"/api/v1/sla/policies/{sla_policy.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(sla_policy.id)


@pytest.mark.asyncio
async def test_update_policy(admin_client: AsyncClient, sla_policy: SlaPolicy):
    resp = await admin_client.patch(
        f"/api/v1/sla/policies/{sla_policy.id}",
        json={"attendance_minutes": 90},
    )
    assert resp.status_code == 200
    assert resp.json()["attendance_minutes"] == 90


@pytest.mark.asyncio
async def test_deactivate_policy(admin_client: AsyncClient, sla_policy: SlaPolicy):
    resp = await admin_client.post(f"/api/v1/sla/policies/{sla_policy.id}/deactivate")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_create_duplicate_policy_rejected(
    admin_client: AsyncClient, sla_policy: SlaPolicy, default_priority: Priority
):
    resp = await admin_client.post(
        "/api/v1/sla/policies",
        json={
            "ticket_type": "predial",
            "priority_id": str(default_priority.id),
            "attendance_minutes": 30,
            "resolution_minutes": 240,
        },
    )
    assert resp.status_code == 422


# ── SLA Lifecycle ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_initialize_tracker_on_creation(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sla_policy: SlaPolicy,
    default_priority: Priority,
):
    svc = _make_svc(db_session, seeded_tenant.id)
    ticket_id = uuid4()
    created_at = datetime.utcnow()

    await svc.initialize_tracker(
        ticket_id=ticket_id,
        ticket_type="predial",
        priority_id=default_priority.id,
        team_id=None,
        created_at=created_at,
    )

    tracker = await _get_tracker(db_session, ticket_id, seeded_tenant.id)
    assert tracker is not None
    assert tracker.attendance_due_at == created_at + timedelta(minutes=60)
    assert tracker.attendance_status == "running"
    assert tracker.resolution_due_at is None


@pytest.mark.asyncio
async def test_no_tracker_when_no_policy(
    db_session: AsyncSession, seeded_tenant: Tenant, high_priority: Priority
):
    # high_priority has no SLA policy → no tracker
    svc = _make_svc(db_session, seeded_tenant.id)
    ticket_id = uuid4()

    await svc.initialize_tracker(
        ticket_id=ticket_id,
        ticket_type="industrial",
        priority_id=high_priority.id,
        team_id=None,
        created_at=datetime.utcnow(),
    )

    tracker = await _get_tracker(db_session, ticket_id, seeded_tenant.id)
    assert tracker is None


@pytest.mark.asyncio
async def test_full_lifecycle(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sla_policy: SlaPolicy,
    default_priority: Priority,
):
    """Create → Assign (met) → Pending → Resume → Resolve (met)."""
    svc = _make_svc(db_session, seeded_tenant.id)
    ticket_id = uuid4()
    t0 = datetime(2026, 1, 1, 8, 0)

    # Initialize
    await svc.initialize_tracker(
        ticket_id=ticket_id,
        ticket_type="predial",
        priority_id=default_priority.id,
        team_id=None,
        created_at=t0,
    )
    tracker = await _get_tracker(db_session, ticket_id, seeded_tenant.id)
    assert tracker.attendance_due_at == t0 + timedelta(minutes=60)

    # Assign (within SLA)
    t1 = t0 + timedelta(minutes=30)  # 30 min after creation → within 60 min limit
    await svc.on_ticket_assigned(ticket_id=ticket_id, assigned_at=t1)
    await db_session.refresh(tracker)
    assert tracker.attendance_status == "met"
    expected_resolution_due = t1 + timedelta(minutes=480)
    assert tracker.resolution_due_at == expected_resolution_due

    # Pending (pause SLA)
    t2 = t0 + timedelta(hours=2)
    await svc.on_ticket_pending(ticket_id=ticket_id, paused_at=t2)
    await db_session.refresh(tracker)
    assert tracker.resolution_status == "paused"

    # Resume after 30 min pause
    t3 = t2 + timedelta(minutes=30)
    await svc.on_ticket_resumed(ticket_id=ticket_id, resumed_at=t3)
    await db_session.refresh(tracker)
    assert tracker.resolution_status == "running"
    assert tracker.total_paused_minutes == 30
    # Deadline extended by 30 minutes
    assert tracker.resolution_due_at == expected_resolution_due + timedelta(minutes=30)

    # Resolve before deadline
    t4 = tracker.resolution_due_at - timedelta(minutes=60)
    await svc.on_ticket_resolved(ticket_id=ticket_id, resolved_at=t4)
    await db_session.refresh(tracker)
    assert tracker.resolution_status == "met"


@pytest.mark.asyncio
async def test_breach_sweep_marks_overdue(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sla_policy: SlaPolicy,
    default_priority: Priority,
):
    svc = _make_svc(db_session, seeded_tenant.id)
    ticket_id = uuid4()
    # Set created_at far in the past so attendance_due_at is already passed
    past = datetime.utcnow() - timedelta(hours=5)

    await svc.initialize_tracker(
        ticket_id=ticket_id,
        ticket_type="predial",
        priority_id=default_priority.id,
        team_id=None,
        created_at=past,
    )

    await svc.sweep_breaches()

    tracker = await _get_tracker(db_session, ticket_id, seeded_tenant.id)
    assert tracker.attendance_status == "breached"


@pytest.mark.asyncio
async def test_breach_sweep_idempotent(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sla_policy: SlaPolicy,
    default_priority: Priority,
):
    svc = _make_svc(db_session, seeded_tenant.id)
    ticket_id = uuid4()
    past = datetime.utcnow() - timedelta(hours=5)

    await svc.initialize_tracker(
        ticket_id=ticket_id,
        ticket_type="predial",
        priority_id=default_priority.id,
        team_id=None,
        created_at=past,
    )
    await svc.sweep_breaches()
    await svc.sweep_breaches()  # second run should be idempotent

    tracker = await _get_tracker(db_session, ticket_id, seeded_tenant.id)
    assert tracker.attendance_status == "breached"  # not changed twice


@pytest.mark.asyncio
async def test_get_ticket_sla_returns_tracker(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sla_policy: SlaPolicy,
    default_priority: Priority,
):
    svc = _make_svc(db_session, seeded_tenant.id)
    ticket_id = uuid4()
    await svc.initialize_tracker(
        ticket_id=ticket_id,
        ticket_type="predial",
        priority_id=default_priority.id,
        team_id=None,
        created_at=datetime.utcnow(),
    )
    await db_session.flush()

    resp = await admin_client.get(f"/api/v1/tickets/{ticket_id}/sla")
    assert resp.status_code == 200
    data = resp.json()
    assert data["policy_id"] == str(sla_policy.id)
    assert data["attendance"]["status"] == "running"


@pytest.mark.asyncio
async def test_get_ticket_sla_404_no_tracker(admin_client: AsyncClient):
    resp = await admin_client.get(f"/api/v1/tickets/{uuid4()}/sla")
    assert resp.status_code == 404
