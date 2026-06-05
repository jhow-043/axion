"""Tenant isolation tests for P14 — Notificações.

Verifies that users from tenant A cannot see or act on notifications from tenant B.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.modules.notifications.models import Notification
from app.modules.tenants.models import Tenant
from app.modules.users.models import User
from app.shared.tenant_context import tenant_context

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def iso_tenant_a(db_session: AsyncSession) -> Tenant:
    t = Tenant(id=uuid4(), name="Tenant A", slug=f"iso-a-{uuid4().hex[:6]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def iso_tenant_b(db_session: AsyncSession) -> Tenant:
    t = Tenant(id=uuid4(), name="Tenant B", slug=f"iso-b-{uuid4().hex[:6]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def iso_user_a(db_session: AsyncSession, iso_tenant_a: Tenant) -> User:
    u = User(
        id=uuid4(),
        tenant_id=iso_tenant_a.id,
        name="User A",
        email=f"ua-{uuid4().hex[:6]}@test.com",
        password_hash=hash_password("p"),
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
async def iso_user_b(db_session: AsyncSession, iso_tenant_b: Tenant) -> User:
    u = User(
        id=uuid4(),
        tenant_id=iso_tenant_b.id,
        name="User B",
        email=f"ub-{uuid4().hex[:6]}@test.com",
        password_hash=hash_password("p"),
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
async def iso_notif_for_user_b(
    db_session: AsyncSession,
    iso_tenant_b: Tenant,
    iso_user_b: User,
) -> Notification:
    notif = Notification(
        id=uuid4(),
        tenant_id=iso_tenant_b.id,
        recipient_id=iso_user_b.id,
        ticket_id=None,
        event_type="ticket_assigned",
        title="Notif de B",
        body="Corpo de B",
    )
    db_session.add(notif)
    await db_session.flush()
    return notif


@pytest.fixture
def iso_token_a(iso_user_a: User, iso_tenant_a: Tenant) -> str:
    return create_access_token(str(iso_user_a.id), iso_tenant_a.id, [])


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_notifications_isolated(
    async_client: AsyncClient,
    iso_notif_for_user_b: Notification,
    iso_token_a: str,
    iso_tenant_a: Tenant,
):
    """INV-01: user from tenant A cannot see notifications belonging to tenant B."""
    with tenant_context(iso_tenant_a.id):
        resp = await async_client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {iso_token_a}"},
        )
    assert resp.status_code == 200
    ids = [n["id"] for n in resp.json()["items"]]
    assert str(iso_notif_for_user_b.id) not in ids


@pytest.mark.asyncio
async def test_mark_read_cross_tenant_returns_404(
    async_client: AsyncClient,
    iso_notif_for_user_b: Notification,
    iso_token_a: str,
    iso_tenant_a: Tenant,
):
    """INV-02: accessing another tenant's notification must return 404, not 403."""
    with tenant_context(iso_tenant_a.id):
        resp = await async_client.post(
            f"/api/v1/notifications/{iso_notif_for_user_b.id}/read",
            headers={"Authorization": f"Bearer {iso_token_a}"},
        )
    # BaseRepository.get() with cross-tenant ID returns None → 404
    assert resp.status_code == 404
