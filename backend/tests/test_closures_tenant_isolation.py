"""Tenant isolation tests for P13 — INV-01 and INV-02 compliance."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.modules.catalog.models import Priority, Status
from app.modules.closures.models import Validation
from app.modules.closures.repository import ValidationRepository
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import User
from app.shared.tenant_context import tenant_context


@pytest.fixture
async def tenant_iso_a(db_session: AsyncSession) -> Tenant:
    t = Tenant(id=uuid4(), name="Iso A", slug=f"iso-a-{uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def tenant_iso_b(db_session: AsyncSession) -> Tenant:
    t = Tenant(id=uuid4(), name="Iso B", slug=f"iso-b-{uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


async def _mk_user(session, tenant_id):
    u = User(
        id=uuid4(),
        tenant_id=tenant_id,
        name="U",
        email=f"u-{uuid4().hex[:6]}@t.com",
        password_hash=hash_password("x"),
    )
    session.add(u)
    await session.flush()
    return u


async def _mk_status(session, tenant_id, code="resolved"):
    s = Status(id=uuid4(), tenant_id=tenant_id, name=code, code=code, order=1)
    session.add(s)
    await session.flush()
    return s


async def _mk_priority(session, tenant_id):
    p = Priority(id=uuid4(), tenant_id=tenant_id, name="A", code="a", order=1)
    session.add(p)
    await session.flush()
    return p


async def _mk_ticket(session, tenant_id, user_id, status_id, priority_id):
    t = Ticket(
        id=uuid4(),
        tenant_id=tenant_id,
        type="predial",
        title="T",
        description="d",
        priority_id=priority_id,
        status_id=status_id,
        requester_id=user_id,
    )
    session.add(t)
    await session.flush()
    return t


async def _mk_validation(session, tenant_id, ticket_id, requester_id, *, days_offset=5):
    v = Validation(
        id=uuid4(),
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        requester_id=requester_id,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(days=days_offset),
    )
    session.add(v)
    await session.flush()
    return v


class TestValidationTenantIsolation:
    async def test_get_cross_tenant_returns_none(
        self, db_session: AsyncSession, tenant_iso_a: Tenant, tenant_iso_b: Tenant
    ):
        """INV-02: get() with cross-tenant ID returns None → router raises 404."""
        user_b = await _mk_user(db_session, tenant_iso_b.id)
        status_b = await _mk_status(db_session, tenant_iso_b.id)
        priority_b = await _mk_priority(db_session, tenant_iso_b.id)
        ticket_b = await _mk_ticket(
            db_session, tenant_iso_b.id, user_b.id, status_b.id, priority_b.id
        )
        val_b = await _mk_validation(db_session, tenant_iso_b.id, ticket_b.id, user_b.id)

        with tenant_context(tenant_iso_a.id):
            repo_a = ValidationRepository(db_session, tenant_iso_a.id)
            result = await repo_a.get(val_b.id)

        assert result is None

    async def test_find_by_ticket_scoped_to_tenant(
        self, db_session: AsyncSession, tenant_iso_a: Tenant, tenant_iso_b: Tenant
    ):
        user_b = await _mk_user(db_session, tenant_iso_b.id)
        status_b = await _mk_status(db_session, tenant_iso_b.id)
        priority_b = await _mk_priority(db_session, tenant_iso_b.id)
        ticket_b = await _mk_ticket(
            db_session, tenant_iso_b.id, user_b.id, status_b.id, priority_b.id
        )
        await _mk_validation(db_session, tenant_iso_b.id, ticket_b.id, user_b.id)

        with tenant_context(tenant_iso_a.id):
            repo_a = ValidationRepository(db_session, tenant_iso_a.id)
            result = await repo_a.find_by_ticket(ticket_b.id)

        assert result is None

    async def test_list_expired_pending_excludes_other_tenant(
        self, db_session: AsyncSession, tenant_iso_a: Tenant, tenant_iso_b: Tenant
    ):
        user_b = await _mk_user(db_session, tenant_iso_b.id)
        status_b = await _mk_status(db_session, tenant_iso_b.id)
        priority_b = await _mk_priority(db_session, tenant_iso_b.id)
        ticket_b = await _mk_ticket(
            db_session, tenant_iso_b.id, user_b.id, status_b.id, priority_b.id
        )
        val_b = await _mk_validation(
            db_session, tenant_iso_b.id, ticket_b.id, user_b.id, days_offset=-1
        )

        with tenant_context(tenant_iso_a.id):
            repo_a = ValidationRepository(db_session, tenant_iso_a.id)
            expired = await repo_a.list_expired_pending(datetime.utcnow())

        assert val_b.id not in [v.id for v in expired]
        assert all(v.tenant_id == tenant_iso_a.id for v in expired)
