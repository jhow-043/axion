"""Integration tests for P14 — Notificações.

Tests HTTP endpoints against the in-memory SQLite DB (via conftest fixtures).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.modules.catalog.models import Priority, Status
from app.modules.notifications.models import Notification
from app.modules.notifications.repository import (
    NotificationPreferenceRepository,
    NotificationRepository,
)
from app.modules.notifications.service import NotificationService
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Ticket
from app.modules.users.models import User
from app.shared.tenant_context import tenant_context

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def nt_tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(id=uuid4(), name="Notif Corp", slug=f"nt-{uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def nt_user(db_session: AsyncSession, nt_tenant: Tenant) -> User:
    u = User(
        id=uuid4(),
        tenant_id=nt_tenant.id,
        name="Usuário Notif",
        email=f"notif-{uuid4().hex[:6]}@test.com",
        password_hash=hash_password("p"),
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
async def nt_other_user(db_session: AsyncSession, nt_tenant: Tenant) -> User:
    u = User(
        id=uuid4(),
        tenant_id=nt_tenant.id,
        name="Outro Usuário",
        email=f"other-{uuid4().hex[:6]}@test.com",
        password_hash=hash_password("p"),
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
async def nt_status(db_session: AsyncSession, nt_tenant: Tenant) -> Status:
    s = Status(id=uuid4(), tenant_id=nt_tenant.id, name="Novo", code="new", order=1)
    db_session.add(s)
    await db_session.flush()
    return s


@pytest.fixture
async def nt_priority(db_session: AsyncSession, nt_tenant: Tenant) -> Priority:
    p = Priority(id=uuid4(), tenant_id=nt_tenant.id, name="Média", code="medium", order=2)
    db_session.add(p)
    await db_session.flush()
    return p


@pytest.fixture
async def nt_ticket(
    db_session: AsyncSession,
    nt_tenant: Tenant,
    nt_user: User,
    nt_status: Status,
    nt_priority: Priority,
) -> Ticket:
    t = Ticket(
        id=uuid4(),
        tenant_id=nt_tenant.id,
        type="predial",
        title="Luz apagada",
        description="Corredor escuro",
        priority_id=nt_priority.id,
        status_id=nt_status.id,
        requester_id=nt_user.id,
    )
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
def nt_token(nt_user: User, nt_tenant: Tenant) -> str:
    return create_access_token(str(nt_user.id), nt_tenant.id, [])


@pytest.fixture
def nt_other_token(nt_other_user: User, nt_tenant: Tenant) -> str:
    return create_access_token(str(nt_other_user.id), nt_tenant.id, [])


@pytest.fixture
async def nt_notification(
    db_session: AsyncSession,
    nt_tenant: Tenant,
    nt_user: User,
    nt_ticket: Ticket,
) -> Notification:
    notif = Notification(
        id=uuid4(),
        tenant_id=nt_tenant.id,
        recipient_id=nt_user.id,
        ticket_id=nt_ticket.id,
        event_type="ticket_assigned",
        title="Chamado atribuído",
        body="O chamado foi atribuído.",
    )
    db_session.add(notif)
    await db_session.flush()
    return notif


# ── GET /notifications ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_notifications_returns_own(
    async_client: AsyncClient,
    nt_notification: Notification,
    nt_token: str,
    nt_tenant: Tenant,
):
    with tenant_context(nt_tenant.id):
        resp = await async_client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {nt_token}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    ids = [n["id"] for n in data["items"]]
    assert str(nt_notification.id) in ids


@pytest.mark.asyncio
async def test_list_notifications_filter_unread(
    async_client: AsyncClient,
    nt_notification: Notification,
    nt_token: str,
    nt_tenant: Tenant,
):
    with tenant_context(nt_tenant.id):
        resp = await async_client.get(
            "/api/v1/notifications?is_read=false",
            headers={"Authorization": f"Bearer {nt_token}"},
        )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(not n["is_read"] for n in items)


# ── POST /notifications/{id}/read ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mark_read_own_notification(
    async_client: AsyncClient,
    nt_notification: Notification,
    nt_token: str,
    nt_tenant: Tenant,
):
    with tenant_context(nt_tenant.id):
        resp = await async_client.post(
            f"/api/v1/notifications/{nt_notification.id}/read",
            headers={"Authorization": f"Bearer {nt_token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


@pytest.mark.asyncio
async def test_mark_read_other_user_returns_403(
    async_client: AsyncClient,
    nt_notification: Notification,
    nt_other_token: str,
    nt_tenant: Tenant,
):
    """RN-04 (spec): another user cannot mark someone else's notification as read."""
    with tenant_context(nt_tenant.id):
        resp = await async_client.post(
            f"/api/v1/notifications/{nt_notification.id}/read",
            headers={"Authorization": f"Bearer {nt_other_token}"},
        )
    assert resp.status_code == 403


# ── POST /notifications/read-all ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mark_all_read(
    async_client: AsyncClient,
    nt_notification: Notification,
    nt_token: str,
    nt_tenant: Tenant,
):
    with tenant_context(nt_tenant.id):
        resp = await async_client.post(
            "/api/v1/notifications/read-all",
            headers={"Authorization": f"Bearer {nt_token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["marked_read"] >= 1


# ── GET /notifications/preferences ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_preferences_empty(
    async_client: AsyncClient,
    nt_token: str,
    nt_tenant: Tenant,
):
    with tenant_context(nt_tenant.id):
        resp = await async_client.get(
            "/api/v1/notifications/preferences",
            headers={"Authorization": f"Bearer {nt_token}"},
        )
    assert resp.status_code == 200
    assert "preferences" in resp.json()


# ── PATCH /notifications/preferences ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_preferences(
    async_client: AsyncClient,
    nt_token: str,
    nt_tenant: Tenant,
):
    payload = {
        "preferences": [
            {"event_type": "ticket_comment_added", "in_app_enabled": True, "email_enabled": False}
        ]
    }
    with tenant_context(nt_tenant.id):
        resp = await async_client.patch(
            "/api/v1/notifications/preferences",
            json=payload,
            headers={"Authorization": f"Bearer {nt_token}"},
        )
    assert resp.status_code == 200
    prefs = resp.json()["preferences"]
    matching = [p for p in prefs if p["event_type"] == "ticket_comment_added"]
    assert matching[0]["email_enabled"] is False


# ── notify() integration ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_notify_persists_notification(
    db_session: AsyncSession,
    nt_tenant: Tenant,
    nt_user: User,
    nt_ticket: Ticket,
):
    """CA: notify() → notification persisted for each recipient."""
    with tenant_context(nt_tenant.id):
        notif_repo = NotificationRepository(db_session, nt_tenant.id)
        pref_repo = NotificationPreferenceRepository(db_session, nt_tenant.id)

        svc = NotificationService(
            notification_repo=notif_repo,
            preference_repo=pref_repo,
            redis_url=None,
        )

        # Inject ticket to make resolution work:
        # ticket_assigned → requester + observers; requester = nt_user
        from unittest.mock import AsyncMock, MagicMock

        ticket = MagicMock()
        ticket.requester_id = nt_user.id
        ticket.assignee_id = None
        ticket.team_id = None

        from app.modules.notifications.repository import RecipientQueryRepository

        recipient_repo = AsyncMock(spec=RecipientQueryRepository)
        recipient_repo.get_observer_user_ids = AsyncMock(return_value=[])
        recipient_repo.get_users_by_role_codes = AsyncMock(return_value=[])
        recipient_repo.get_team_users_by_role_codes = AsyncMock(return_value=[])
        recipient_repo.get_user_email = AsyncMock(return_value=None)

        ticket_repo = AsyncMock()
        ticket_repo.get = AsyncMock(return_value=ticket)

        svc._tickets = ticket_repo
        svc._recipients = recipient_repo

        actor_id = uuid4()  # different from requester
        await svc.notify(
            event_type="ticket_assigned",
            ticket_id=nt_ticket.id,
            actor_id=actor_id,
        )
        await db_session.flush()

        count = await notif_repo.count_for_recipient(nt_user.id)
        assert count >= 1


@pytest.mark.asyncio
async def test_notify_email_preference_respected(
    db_session: AsyncSession,
    nt_tenant: Tenant,
    nt_user: User,
    nt_ticket: Ticket,
):
    """CA: email_enabled=False for event type → email task not enqueued."""
    with tenant_context(nt_tenant.id):
        notif_repo = NotificationRepository(db_session, nt_tenant.id)
        pref_repo = NotificationPreferenceRepository(db_session, nt_tenant.id)

        # Set email opt-out for this event
        await pref_repo.upsert(
            user_id=nt_user.id,
            event_type="ticket_comment_added",
            in_app_enabled=True,
            email_enabled=False,
        )
        await db_session.flush()

        from unittest.mock import AsyncMock, MagicMock, patch

        ticket = MagicMock()
        ticket.requester_id = nt_user.id
        ticket.assignee_id = None
        ticket.team_id = None

        from app.modules.notifications.repository import RecipientQueryRepository

        recipient_repo = AsyncMock(spec=RecipientQueryRepository)
        recipient_repo.get_observer_user_ids = AsyncMock(return_value=[])
        recipient_repo.get_users_by_role_codes = AsyncMock(return_value=[])
        recipient_repo.get_team_users_by_role_codes = AsyncMock(return_value=[])
        recipient_repo.get_user_email = AsyncMock(return_value="user@test.com")

        ticket_repo = AsyncMock()
        ticket_repo.get = AsyncMock(return_value=ticket)

        svc = NotificationService(
            notification_repo=notif_repo,
            preference_repo=pref_repo,
            ticket_repo=ticket_repo,
            recipient_repo=recipient_repo,
            redis_url=None,
        )

        with patch("celery.current_app.send_task") as mock_send:
            await svc.notify(
                event_type="ticket_comment_added",
                ticket_id=nt_ticket.id,
                actor_id=uuid4(),
            )
            mock_send.assert_not_called()
