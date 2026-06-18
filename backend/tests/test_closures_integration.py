"""Integration tests for P13 — Encerramento, Validação e Auto-Fechamento.
Fixtures are defined inline; shared infra fixtures (db_session, async_client) from conftest.py."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.modules.catalog.models import Priority, Status
from app.modules.catalog.repository import StatusRepository
from app.modules.closures.models import Validation
from app.modules.closures.repository import TenantSettingsRepository, ValidationRepository
from app.modules.closures.service import ClosureService
from app.modules.notifications.service import NotificationService
from app.modules.tenants.models import Tenant
from app.modules.tickets.models import Solution, Ticket
from app.modules.tickets.repository import (
    SolutionRepository,
    TicketObserverRepository,
    TicketRepository,
)
from app.modules.timeline.repository import TicketEventRepository
from app.modules.timeline.service import TimelineService
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.hub.seed import seed_manutencao_for_tenant
from app.shared.tenant_context import tenant_context

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def cl_tenant(db_session: AsyncSession) -> Tenant:
    t = Tenant(id=uuid4(), name="Closures Corp", slug=f"cl-{uuid4().hex[:8]}")
    db_session.add(t)
    await db_session.flush()
    await seed_manutencao_for_tenant(db_session, t.id)
    return t


@pytest.fixture
async def cl_requester(db_session: AsyncSession, cl_tenant: Tenant) -> User:
    u = User(
        id=uuid4(),
        tenant_id=cl_tenant.id,
        name="Solicitante",
        email=f"req-{uuid4().hex[:6]}@test.com",
        password_hash=hash_password("p"),
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
async def cl_other_user(db_session: AsyncSession, cl_tenant: Tenant) -> User:
    u = User(
        id=uuid4(),
        tenant_id=cl_tenant.id,
        name="Outro",
        email=f"other-{uuid4().hex[:6]}@test.com",
        password_hash=hash_password("p"),
    )
    db_session.add(u)
    await db_session.flush()
    return u


@pytest.fixture
async def cl_status_resolved(db_session: AsyncSession, cl_tenant: Tenant) -> Status:
    s = Status(id=uuid4(), tenant_id=cl_tenant.id, name="Solucionado", code="resolved", order=4)
    db_session.add(s)
    await db_session.flush()
    return s


@pytest.fixture
async def cl_status_closed(db_session: AsyncSession, cl_tenant: Tenant) -> Status:
    s = Status(id=uuid4(), tenant_id=cl_tenant.id, name="Fechado", code="closed", order=5)
    db_session.add(s)
    await db_session.flush()
    return s


@pytest.fixture
async def cl_status_in_progress(db_session: AsyncSession, cl_tenant: Tenant) -> Status:
    s = Status(
        id=uuid4(), tenant_id=cl_tenant.id, name="Em Atendimento", code="in_progress", order=2
    )
    db_session.add(s)
    await db_session.flush()
    return s


@pytest.fixture
async def cl_priority(db_session: AsyncSession, cl_tenant: Tenant) -> Priority:
    p = Priority(id=uuid4(), tenant_id=cl_tenant.id, name="Alta", code="high", order=1)
    db_session.add(p)
    await db_session.flush()
    return p


@pytest.fixture
async def cl_ticket(
    db_session: AsyncSession,
    cl_tenant: Tenant,
    cl_requester: User,
    cl_status_resolved: Status,
    cl_priority: Priority,
) -> Ticket:
    t = Ticket(
        id=uuid4(),
        tenant_id=cl_tenant.id,
        type="predial",
        title="Ticket P13",
        description="desc",
        priority_id=cl_priority.id,
        status_id=cl_status_resolved.id,
        requester_id=cl_requester.id,
    )
    db_session.add(t)
    await db_session.flush()
    return t


@pytest.fixture
async def cl_solution(
    db_session: AsyncSession, cl_tenant: Tenant, cl_ticket: Ticket, cl_requester: User
) -> Solution:
    s = Solution(
        id=uuid4(),
        tenant_id=cl_tenant.id,
        ticket_id=cl_ticket.id,
        description="Problema resolvido.",
        resolved_by=cl_requester.id,
        resolved_at=datetime.utcnow(),
    )
    db_session.add(s)
    await db_session.flush()
    return s


@pytest.fixture
async def cl_validation(
    db_session: AsyncSession, cl_tenant: Tenant, cl_ticket: Ticket, cl_requester: User
) -> Validation:
    v = Validation(
        id=uuid4(),
        tenant_id=cl_tenant.id,
        ticket_id=cl_ticket.id,
        requester_id=cl_requester.id,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(days=5),
    )
    db_session.add(v)
    await db_session.flush()
    return v


@pytest.fixture
async def cl_expired_validation(
    db_session: AsyncSession, cl_tenant: Tenant, cl_ticket: Ticket, cl_requester: User
) -> Validation:
    v = Validation(
        id=uuid4(),
        tenant_id=cl_tenant.id,
        ticket_id=cl_ticket.id,
        requester_id=cl_requester.id,
        status="pending",
        expires_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add(v)
    await db_session.flush()
    return v


# ── Helpers ───────────────────────────────────────────────────────────────────


def _auth(user, tenant):
    token = create_access_token(str(user.id), tenant.id, ["admin"])
    return {"Authorization": f"Bearer {token}"}


def _svc(session, tenant_id):
    return ClosureService(
        validation_repo=ValidationRepository(session, tenant_id),
        settings_repo=TenantSettingsRepository(session, tenant_id),
        ticket_repo=TicketRepository(session, tenant_id),
        solution_repo=SolutionRepository(session, tenant_id),
        status_repo=StatusRepository(session, tenant_id),
        user_repo=UserRepository(session, tenant_id),
        timeline_svc=TimelineService(
            event_repo=TicketEventRepository(session, tenant_id),
            ticket_repo=TicketRepository(session, tenant_id),
            observer_repo=TicketObserverRepository(session, tenant_id),
            user_repo=UserRepository(session, tenant_id),
        ),
        notification_svc=NotificationService(),
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestGetValidation:
    async def test_returns_validation_with_solution(
        self,
        async_client: AsyncClient,
        cl_tenant,
        cl_requester,
        cl_ticket,
        cl_solution,
        cl_validation,
    ):
        with patch("app.modules.auth.repository.UserAuthRepository.get_permissions") as mp:
            mp.return_value = {"ticket:read"}
            resp = await async_client.get(
                f"/api/v1/tickets/{cl_ticket.id}/validation",
                headers=_auth(cl_requester, cl_tenant),
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "pending"
        assert body["days_remaining"] >= 4
        assert body["solution"]["description"] == "Problema resolvido."

    async def test_returns_404_if_no_validation(
        self, async_client: AsyncClient, cl_tenant, cl_requester, cl_ticket
    ):
        with patch("app.modules.auth.repository.UserAuthRepository.get_permissions") as mp:
            mp.return_value = {"ticket:read"}
            resp = await async_client.get(
                f"/api/v1/tickets/{cl_ticket.id}/validation",
                headers=_auth(cl_requester, cl_tenant),
            )

        assert resp.status_code == 404


class TestApproveValidation:
    async def test_requester_approves_closes_ticket(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        cl_tenant,
        cl_requester,
        cl_ticket,
        cl_solution,
        cl_validation,
        cl_status_closed,
    ):
        with patch("app.modules.auth.repository.UserAuthRepository.get_permissions") as mp:
            mp.return_value = {"ticket:validate"}
            resp = await async_client.post(
                f"/api/v1/tickets/{cl_ticket.id}/validation/approve",
                headers=_auth(cl_requester, cl_tenant),
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

        with tenant_context(cl_tenant.id):
            ticket = await TicketRepository(db_session, cl_tenant.id).get(cl_ticket.id)
        assert ticket.status_id == cl_status_closed.id
        assert ticket.closed_at is not None

    async def test_other_user_cannot_approve(
        self,
        async_client: AsyncClient,
        cl_tenant,
        cl_other_user,
        cl_ticket,
        cl_solution,
        cl_validation,
    ):
        with patch("app.modules.auth.repository.UserAuthRepository.get_permissions") as mp:
            mp.return_value = {"ticket:validate"}
            resp = await async_client.post(
                f"/api/v1/tickets/{cl_ticket.id}/validation/approve",
                headers=_auth(cl_other_user, cl_tenant),
            )

        assert resp.status_code == 403


class TestRejectValidation:
    async def test_reject_without_reason_returns_422(
        self, async_client: AsyncClient, cl_tenant, cl_requester, cl_ticket, cl_validation
    ):
        with patch("app.modules.auth.repository.UserAuthRepository.get_permissions") as mp:
            mp.return_value = {"ticket:validate"}
            resp = await async_client.post(
                f"/api/v1/tickets/{cl_ticket.id}/validation/reject",
                json={"rejection_reason": ""},
                headers=_auth(cl_requester, cl_tenant),
            )

        assert resp.status_code == 422

    async def test_requester_rejects_reopens_ticket(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        cl_tenant,
        cl_requester,
        cl_ticket,
        cl_solution,
        cl_validation,
        cl_status_in_progress,
    ):
        with patch("app.modules.auth.repository.UserAuthRepository.get_permissions") as mp:
            mp.return_value = {"ticket:validate"}
            resp = await async_client.post(
                f"/api/v1/tickets/{cl_ticket.id}/validation/reject",
                json={"rejection_reason": "O problema persiste."},
                headers=_auth(cl_requester, cl_tenant),
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

        with tenant_context(cl_tenant.id):
            ticket = await TicketRepository(db_session, cl_tenant.id).get(cl_ticket.id)
        assert ticket.status_id == cl_status_in_progress.id


class TestAdminSettings:
    async def test_patch_settings_persists_new_auto_close_days(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        cl_tenant,
        cl_requester,
    ):
        with patch("app.modules.auth.repository.UserAuthRepository.get_permissions") as mp:
            mp.return_value = {"admin:config"}
            resp = await async_client.patch(
                "/api/v1/admin/settings",
                json={"auto_close_days": 10},
                headers=_auth(cl_requester, cl_tenant),
            )

        assert resp.status_code == 200
        assert resp.json()["auto_close_days"] == 10

        # Validate that next validation uses 10 days
        with tenant_context(cl_tenant.id):
            svc = _svc(db_session, cl_tenant.id)
            ticket_id = uuid4()
            await svc.create_validation(ticket_id=ticket_id, requester_id=cl_requester.id)
            val = await ValidationRepository(db_session, cl_tenant.id).find_by_ticket(ticket_id)

        diff = val.expires_at - datetime.utcnow()
        assert 9 <= diff.days <= 10

    async def test_get_settings_returns_defaults(
        self, async_client: AsyncClient, cl_tenant, cl_requester
    ):
        with patch("app.modules.auth.repository.UserAuthRepository.get_permissions") as mp:
            mp.return_value = {"admin:config"}
            resp = await async_client.get(
                "/api/v1/admin/settings",
                headers=_auth(cl_requester, cl_tenant),
            )

        assert resp.status_code == 200
        assert resp.json()["auto_close_days"] == 5


class TestAutoCloseSweep:
    async def test_sweep_closes_expired_pending(
        self,
        db_session: AsyncSession,
        cl_tenant,
        cl_ticket,
        cl_solution,
        cl_expired_validation,
        cl_status_closed,
        cl_status_in_progress,
    ):
        with tenant_context(cl_tenant.id):
            svc = _svc(db_session, cl_tenant.id)
            await svc.sweep_auto_close()

            val = await ValidationRepository(db_session, cl_tenant.id).get(cl_expired_validation.id)
            assert val.status == "approved"

            ticket = await TicketRepository(db_session, cl_tenant.id).get(cl_ticket.id)
            assert ticket.status_id == cl_status_closed.id

    async def test_sweep_idempotent_on_already_closed(
        self,
        db_session: AsyncSession,
        cl_tenant,
        cl_ticket,
        cl_solution,
        cl_expired_validation,
        cl_status_closed,
        cl_status_in_progress,
    ):
        with tenant_context(cl_tenant.id):
            svc = _svc(db_session, cl_tenant.id)
            await svc.sweep_auto_close()
            await svc.sweep_auto_close()  # second sweep — no-op

            val = await ValidationRepository(db_session, cl_tenant.id).get(cl_expired_validation.id)
            assert val.status == "approved"
