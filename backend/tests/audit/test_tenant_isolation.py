"""Tenant isolation tests for P17 — audit logs must never cross tenant boundaries."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.repository import AuditLogRepository
from app.modules.audit.service import AuditService
from app.modules.tenants.models import Tenant
from app.modules.users.repository import UserRepository


def _build_audit_service(db_session: AsyncSession, tenant_id) -> AuditService:
    return AuditService(
        audit_repo=AuditLogRepository(db_session, tenant_id),
        user_repo=UserRepository(db_session, tenant_id),
    )


@pytest.fixture
async def tenant_a(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Tenant A", slug=f"tenant-a-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def tenant_b(db_session: AsyncSession) -> Tenant:
    t = Tenant(name="Tenant B", slug=f"tenant-b-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.mark.asyncio
async def test_audit_logs_are_tenant_scoped(
    db_session: AsyncSession, tenant_a: Tenant, tenant_b: Tenant
):
    """Logs created by tenant A are invisible to tenant B's repository."""
    svc_a = _build_audit_service(db_session, tenant_a.id)
    svc_b = _build_audit_service(db_session, tenant_b.id)

    entity_id = uuid.uuid4()
    await svc_a.log(
        action="user.created",
        entity_type="User",
        entity_id=entity_id,
        actor_id=None,
        after={"name": "Tenant A User"},
    )
    await db_session.flush()

    # Tenant B must not see tenant A's log
    result_b = await svc_b.list_logs(page=1, page_size=100)
    ids_b = [item.entity_id for item in result_b.items]
    assert entity_id not in ids_b

    # Tenant A must see its own log
    result_a = await svc_a.list_logs(page=1, page_size=100)
    ids_a = [item.entity_id for item in result_a.items]
    assert entity_id in ids_a


@pytest.mark.asyncio
async def test_get_audit_api_returns_only_own_tenant_logs(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    seeded_tenant: Tenant,
):
    """The GET /audit endpoint must only return logs belonging to the authenticated tenant."""
    other_tenant = Tenant(name="Other Tenant", slug=f"other-{uuid.uuid4().hex[:8]}")
    db_session.add(other_tenant)
    await db_session.flush()

    other_svc = _build_audit_service(db_session, other_tenant.id)
    other_entity_id = uuid.uuid4()
    await other_svc.log(
        action="user.created",
        entity_type="User",
        entity_id=other_entity_id,
        actor_id=None,
    )
    await db_session.flush()

    resp = await admin_client.get("/api/v1/audit")
    assert resp.status_code == 200
    data = resp.json()

    entity_ids = [item["entity_id"] for item in data["items"]]
    assert str(other_entity_id) not in entity_ids
