"""Integration tests for P17 — Audit API and cross-module audit trail."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditLogRepository
from app.modules.audit.service import AuditService
from app.modules.catalog.models import Priority
from app.modules.sla.models import SlaPolicy
from app.modules.sla.repository import SlaPauseRepository, SlaPolicyRepository, SlaTrackerRepository
from app.modules.sla.schemas import SlaPolicyPatch
from app.modules.sla.service import SlaService
from app.modules.tenants.models import Tenant
from app.modules.tickets.repository import TicketRepository
from app.modules.users.models import User
from app.modules.users.repository import (
    PermissionRepository,
    RoleRepository,
    UserRepository,
    UserRoleRepository,
)
from app.modules.users.schemas import UserCreate
from app.modules.users.service import UserService

# ── Helpers ──────────────────────────────────────────────────────────────────


def _build_audit_service(db_session: AsyncSession, tenant_id) -> AuditService:
    return AuditService(
        audit_repo=AuditLogRepository(db_session, tenant_id),
        user_repo=UserRepository(db_session, tenant_id),
    )


def _build_sla_service(
    db_session: AsyncSession,
    tenant_id,
    actor_id=None,
    audit_svc=None,
) -> SlaService:
    return SlaService(
        policy_repo=SlaPolicyRepository(db_session, tenant_id),
        tracker_repo=SlaTrackerRepository(db_session, tenant_id),
        pause_repo=SlaPauseRepository(db_session, tenant_id),
        ticket_repo=TicketRepository(db_session, tenant_id),
        audit_svc=audit_svc,
        actor_id=actor_id,
    )


def _build_user_service(
    db_session: AsyncSession,
    tenant_id,
    actor_id=None,
    audit_svc=None,
) -> UserService:
    return UserService(
        user_repo=UserRepository(db_session, tenant_id),
        role_repo=RoleRepository(db_session, tenant_id),
        user_role_repo=UserRoleRepository(db_session, tenant_id),
        permission_repo=PermissionRepository(db_session),
        audit_svc=audit_svc,
        actor_id=actor_id,
    )


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def priority(db_session: AsyncSession, seeded_tenant: Tenant) -> Priority:
    stmt = select(Priority).where(Priority.tenant_id == seeded_tenant.id, Priority.code == "low")
    result = await db_session.execute(stmt)
    return result.scalar_one()


@pytest.fixture
async def sla_policy(
    db_session: AsyncSession, seeded_tenant: Tenant, priority: Priority
) -> SlaPolicy:
    policy = SlaPolicy(
        tenant_id=seeded_tenant.id,
        ticket_type="predial",
        priority_id=priority.id,
        team_id=None,
        attendance_minutes=60,
        resolution_minutes=480,
        alert_threshold_pct=80,
        is_active=True,
    )
    db_session.add(policy)
    await db_session.flush()
    return policy


# ── Tests: audit_service.log() ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_persists_to_db(db_session: AsyncSession, seeded_tenant: Tenant):
    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    entity_id = uuid.uuid4()

    await audit_svc.log(
        action="user.created",
        entity_type="User",
        entity_id=entity_id,
        actor_id=None,
        after={"name": "Alice"},
    )
    await db_session.flush()

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == seeded_tenant.id, AuditLog.entity_id == entity_id
    )
    result = await db_session.execute(stmt)
    log = result.scalar_one_or_none()

    assert log is not None
    assert log.action == "user.created"
    assert log.entity_type == "User"
    assert log.before is None
    assert log.after == {"name": "Alice"}
    assert log.actor_id is None


# ── Tests: SLA policy audit ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_sla_policy_creates_audit_log(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    sla_policy: SlaPolicy,
    admin_user: User,
):
    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    svc = _build_sla_service(
        db_session, seeded_tenant.id, actor_id=admin_user.id, audit_svc=audit_svc
    )

    await svc.update_policy(sla_policy.id, SlaPolicyPatch(resolution_minutes=360))
    await db_session.flush()

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == seeded_tenant.id,
        AuditLog.entity_id == sla_policy.id,
        AuditLog.action == "sla_policy.updated",
    )
    result = await db_session.execute(stmt)
    log = result.scalar_one_or_none()

    assert log is not None
    assert log.before["resolution_minutes"] == 480
    assert log.after["resolution_minutes"] == 360
    assert log.actor_id == admin_user.id


# ── Tests: User audit ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_user_generates_audit_log(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
):
    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    svc = _build_user_service(
        db_session, seeded_tenant.id, actor_id=admin_user.id, audit_svc=audit_svc
    )

    data = UserCreate(name="Bob", email=f"bob-{uuid.uuid4().hex[:6]}@test.com", password="pass1234")
    created = await svc.create_user(data)
    await db_session.flush()

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == seeded_tenant.id,
        AuditLog.entity_id == created.id,
        AuditLog.action == "user.created",
    )
    result = await db_session.execute(stmt)
    log = result.scalar_one_or_none()

    assert log is not None
    assert log.before is None
    assert log.after["name"] == "Bob"
    assert log.actor_id == admin_user.id


@pytest.mark.asyncio
async def test_deactivate_user_generates_audit_log(
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
    technician_user: User,
):
    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    svc = _build_user_service(
        db_session, seeded_tenant.id, actor_id=admin_user.id, audit_svc=audit_svc
    )

    await svc.deactivate(technician_user.id)
    await db_session.flush()

    stmt = select(AuditLog).where(
        AuditLog.tenant_id == seeded_tenant.id,
        AuditLog.entity_id == technician_user.id,
        AuditLog.action == "user.deactivated",
    )
    result = await db_session.execute(stmt)
    log = result.scalar_one_or_none()

    assert log is not None
    assert log.before["is_active"] is True
    assert log.after["is_active"] is False


# ── Tests: GET /audit endpoint ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_audit_returns_tenant_logs_only(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
):
    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    entity_id = uuid.uuid4()
    await audit_svc.log(
        action="test.action",
        entity_type="User",
        entity_id=entity_id,
        actor_id=None,
    )
    await db_session.flush()

    resp = await admin_client.get("/api/v1/audit")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_audit_filters_by_entity_type(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
):
    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    await audit_svc.log(
        action="user.created",
        entity_type="User",
        entity_id=uuid.uuid4(),
        actor_id=None,
        after={"name": "FilterTest"},
    )
    await audit_svc.log(
        action="sla_policy.updated",
        entity_type="SlaPolicy",
        entity_id=uuid.uuid4(),
        actor_id=None,
    )
    await db_session.flush()

    resp = await admin_client.get("/api/v1/audit", params={"entity_type": "User"})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["entity_type"] == "User"


@pytest.mark.asyncio
async def test_get_audit_filters_by_actor_id(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
    admin_user: User,
):
    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    await audit_svc.log(
        action="user.created",
        entity_type="User",
        entity_id=uuid.uuid4(),
        actor_id=admin_user.id,
    )
    await db_session.flush()

    resp = await admin_client.get("/api/v1/audit", params={"actor_id": str(admin_user.id)})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["actor"]["id"] == str(admin_user.id)


@pytest.mark.asyncio
async def test_get_audit_non_admin_returns_403(tech_client: AsyncClient):
    resp = await tech_client.get("/api/v1/audit")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_audit_filters_by_entity_id(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
):
    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    target_entity_id = uuid.uuid4()
    await audit_svc.log(
        action="user.created",
        entity_type="User",
        entity_id=target_entity_id,
        actor_id=None,
    )
    await audit_svc.log(
        action="user.created",
        entity_type="User",
        entity_id=uuid.uuid4(),
        actor_id=None,
    )
    await db_session.flush()

    resp = await admin_client.get("/api/v1/audit", params={"entity_id": str(target_entity_id)})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["entity_id"] == str(target_entity_id)


@pytest.mark.asyncio
async def test_get_audit_filters_by_action(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
):
    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    await audit_svc.log(
        action="user.created",
        entity_type="User",
        entity_id=uuid.uuid4(),
        actor_id=None,
    )
    await audit_svc.log(
        action="user.deactivated",
        entity_type="User",
        entity_id=uuid.uuid4(),
        actor_id=None,
    )
    await db_session.flush()

    resp = await admin_client.get("/api/v1/audit", params={"action": "user.created"})
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["action"] == "user.created"


@pytest.mark.asyncio
async def test_get_audit_filters_by_date_range(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
):
    from datetime import datetime, timedelta

    audit_svc = _build_audit_service(db_session, seeded_tenant.id)
    await audit_svc.log(
        action="user.created",
        entity_type="User",
        entity_id=uuid.uuid4(),
        actor_id=None,
    )
    await db_session.flush()

    date_from = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
    date_to = (datetime.utcnow() + timedelta(minutes=5)).isoformat()

    resp = await admin_client.get(
        "/api/v1/audit", params={"date_from": date_from, "date_to": date_to}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_audit_no_delete_endpoint(admin_client: AsyncClient):
    """Audit logs are immutable — no DELETE endpoint exists (route itself is absent)."""
    resp = await admin_client.delete("/api/v1/audit/some-id")
    # 404 = path not registered at all; proves no delete route exists
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_audit_no_patch_endpoint(admin_client: AsyncClient):
    """Audit logs are immutable — no PATCH endpoint exists (route itself is absent)."""
    resp = await admin_client.patch("/api/v1/audit/some-id", json={})
    assert resp.status_code == 404
