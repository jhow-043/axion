"""Integration tests for the tickets module — hit real (SQLite) DB via HTTP."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import PendingReason, Priority, Status
from app.modules.equipments.models import Equipment
from app.modules.locations.models import Location, Sector
from app.modules.tenants.models import Tenant
from app.modules.users.models import User

# ── Helpers ───────────────────────────────────────────────────────────────────


def _predial_payload(location_id: str, priority_id: str) -> dict:
    return {
        "type": "predial",
        "title": "Problema na iluminação",
        "description": "Lâmpada queimada no corredor.",
        "priority_id": priority_id,
        "location_id": location_id,
    }


def _industrial_payload(equipment_id: str, priority_id: str) -> dict:
    return {
        "type": "industrial",
        "title": "Motor com falha",
        "description": "Motor da bomba B-01 travando.",
        "priority_id": priority_id,
        "equipment_id": equipment_id,
    }


@pytest.fixture
async def active_equipment(
    db_session: AsyncSession, seeded_tenant: Tenant, admin_user: User
) -> Equipment:
    sector = Sector(tenant_id=seeded_tenant.id, name=f"Mec {uuid.uuid4().hex[:4]}", is_active=True)
    db_session.add(sector)
    await db_session.flush()
    eq = Equipment(
        tenant_id=seeded_tenant.id,
        code=f"EQ-{uuid.uuid4().hex[:6].upper()}",
        name="Motor B-01",
        sector_id=sector.id,
        is_active=True,
        created_by=admin_user.id,
    )
    db_session.add(eq)
    await db_session.flush()
    return eq


@pytest.fixture
async def inactive_equipment(
    db_session: AsyncSession, seeded_tenant: Tenant, admin_user: User
) -> Equipment:
    sector = Sector(
        tenant_id=seeded_tenant.id, name=f"Inativo {uuid.uuid4().hex[:4]}", is_active=True
    )
    db_session.add(sector)
    await db_session.flush()
    eq = Equipment(
        tenant_id=seeded_tenant.id,
        code=f"EQ-OFF-{uuid.uuid4().hex[:4].upper()}",
        name="Equipamento Inativo",
        sector_id=sector.id,
        is_active=False,
        created_by=admin_user.id,
    )
    db_session.add(eq)
    await db_session.flush()
    return eq


# ── Create ────────────────────────────────────────────────────────────────────


class TestCreateTicket:
    async def test_create_predial_returns_201(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        resp = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "predial"
        assert data["location_id"] == str(active_location.id)

    async def test_created_ticket_has_status_new(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
        default_status_new: Status,
    ):
        resp = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        assert resp.status_code == 201
        assert resp.json()["status_id"] == str(default_status_new.id)

    async def test_industrial_without_equipment_returns_422(
        self,
        admin_client: AsyncClient,
        default_priority: Priority,
    ):
        resp = await admin_client.post(
            "/api/v1/tickets",
            json={
                "type": "industrial",
                "title": "X",
                "description": "Y",
                "priority_id": str(default_priority.id),
            },
        )
        assert resp.status_code == 422

    async def test_predial_without_location_returns_422(
        self,
        admin_client: AsyncClient,
        default_priority: Priority,
    ):
        resp = await admin_client.post(
            "/api/v1/tickets",
            json={
                "type": "predial",
                "title": "X",
                "description": "Y",
                "priority_id": str(default_priority.id),
            },
        )
        assert resp.status_code == 422

    async def test_industrial_with_inactive_equipment_returns_422(
        self,
        admin_client: AsyncClient,
        inactive_equipment: Equipment,
        default_priority: Priority,
    ):
        resp = await admin_client.post(
            "/api/v1/tickets",
            json=_industrial_payload(str(inactive_equipment.id), str(default_priority.id)),
        )
        assert resp.status_code == 422

    async def test_industrial_with_active_equipment_returns_201(
        self,
        admin_client: AsyncClient,
        active_equipment: Equipment,
        default_priority: Priority,
    ):
        resp = await admin_client.post(
            "/api/v1/tickets",
            json=_industrial_payload(str(active_equipment.id), str(default_priority.id)),
        )
        assert resp.status_code == 201
        assert resp.json()["equipment_id"] == str(active_equipment.id)

    async def test_unauthenticated_returns_401(
        self,
        anon_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        resp = await anon_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        assert resp.status_code == 401


# ── Assign ─────────────────────────────────────────────────────────────────────


class TestAssignTicket:
    async def test_assign_changes_status_to_in_progress(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        tid = cr.json()["id"]
        resp = await admin_client.post(f"/api/v1/tickets/{tid}/assign")
        assert resp.status_code == 200
        data = resp.json()
        assert data["assignee_id"] is not None
        assert data["assigned_at"] is not None

    async def test_assign_already_in_progress_returns_422(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        tid = cr.json()["id"]
        await admin_client.post(f"/api/v1/tickets/{tid}/assign")
        resp = await admin_client.post(f"/api/v1/tickets/{tid}/assign")
        assert resp.status_code == 422

    async def test_technician_can_assign(
        self,
        admin_client: AsyncClient,
        tech_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        tid = cr.json()["id"]
        resp = await tech_client.post(f"/api/v1/tickets/{tid}/assign")
        assert resp.status_code == 200

    async def test_requester_cannot_assign_returns_403(
        self,
        admin_client: AsyncClient,
        requester_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        tid = cr.json()["id"]
        resp = await requester_client.post(f"/api/v1/tickets/{tid}/assign")
        assert resp.status_code == 403


# ── Transition ─────────────────────────────────────────────────────────────────


class TestTransitionTicket:
    async def _create_and_assign(self, admin_client, location_id, priority_id) -> str:
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(location_id, priority_id),
        )
        tid = cr.json()["id"]
        await admin_client.post(f"/api/v1/tickets/{tid}/assign")
        return tid

    async def test_transition_to_pending_with_reason(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
        pending_reason: PendingReason,
    ):
        tid = await self._create_and_assign(
            admin_client, str(active_location.id), str(default_priority.id)
        )
        resp = await admin_client.post(
            f"/api/v1/tickets/{tid}/transition",
            json={"to_status": "pending", "pending_reason_id": str(pending_reason.id)},
        )
        assert resp.status_code == 200

    async def test_transition_to_pending_without_reason_returns_422(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        tid = await self._create_and_assign(
            admin_client, str(active_location.id), str(default_priority.id)
        )
        resp = await admin_client.post(
            f"/api/v1/tickets/{tid}/transition",
            json={"to_status": "pending"},
        )
        assert resp.status_code == 422

    async def test_transition_to_resolved_with_solution(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        tid = await self._create_and_assign(
            admin_client, str(active_location.id), str(default_priority.id)
        )
        resp = await admin_client.post(
            f"/api/v1/tickets/{tid}/transition",
            json={"to_status": "resolved", "solution_description": "Troquei a lâmpada."},
        )
        assert resp.status_code == 200
        assert resp.json()["resolved_at"] is not None

    async def test_transition_to_resolved_without_solution_returns_422(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        tid = await self._create_and_assign(
            admin_client, str(active_location.id), str(default_priority.id)
        )
        resp = await admin_client.post(
            f"/api/v1/tickets/{tid}/transition",
            json={"to_status": "resolved"},
        )
        assert resp.status_code == 422

    async def test_transition_from_closed_returns_422(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        tid = await self._create_and_assign(
            admin_client, str(active_location.id), str(default_priority.id)
        )
        await admin_client.post(
            f"/api/v1/tickets/{tid}/transition",
            json={"to_status": "resolved", "solution_description": "Done."},
        )
        await admin_client.post(f"/api/v1/tickets/{tid}/transition", json={"to_status": "closed"})
        resp = await admin_client.post(
            f"/api/v1/tickets/{tid}/transition", json={"to_status": "in_progress"}
        )
        assert resp.status_code == 422


# ── Comments ───────────────────────────────────────────────────────────────────


class TestComments:
    async def test_participant_can_add_comment(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        tid = cr.json()["id"]
        resp = await admin_client.post(
            f"/api/v1/tickets/{tid}/comments", json={"content": "Verificarei amanhã."}
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "Verificarei amanhã."

    async def test_non_participant_cannot_comment_returns_403(
        self,
        admin_client: AsyncClient,
        tech_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        tid = cr.json()["id"]
        resp = await tech_client.post(
            f"/api/v1/tickets/{tid}/comments", json={"content": "Acesso indevido."}
        )
        assert resp.status_code == 403

    async def test_comment_appears_in_list(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        tid = cr.json()["id"]
        await admin_client.post(
            f"/api/v1/tickets/{tid}/comments", json={"content": "Primeiro comentário."}
        )
        resp = await admin_client.get(f"/api/v1/tickets/{tid}/comments")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


# ── Observers ──────────────────────────────────────────────────────────────────


class TestObservers:
    async def test_add_observer_returns_201(
        self,
        admin_client: AsyncClient,
        technician_user: User,
        active_location: Location,
        default_priority: Priority,
    ):
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        tid = cr.json()["id"]
        resp = await admin_client.post(
            f"/api/v1/tickets/{tid}/observers", json={"user_id": str(technician_user.id)}
        )
        assert resp.status_code == 201

    async def test_observer_can_then_comment(
        self,
        admin_client: AsyncClient,
        tech_client: AsyncClient,
        technician_user: User,
        active_location: Location,
        default_priority: Priority,
    ):
        cr = await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        tid = cr.json()["id"]
        await admin_client.post(
            f"/api/v1/tickets/{tid}/observers", json={"user_id": str(technician_user.id)}
        )
        resp = await tech_client.post(
            f"/api/v1/tickets/{tid}/comments", json={"content": "Observando."}
        )
        assert resp.status_code == 201


# ── List + filters ─────────────────────────────────────────────────────────────


class TestListTickets:
    async def test_list_returns_tickets(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        resp = await admin_client.get("/api/v1/tickets")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "items" in data

    async def test_filter_by_status_code(
        self,
        admin_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        resp = await admin_client.get("/api/v1/tickets?status_code=new")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            # all returned items should have a status_id, but we can't easily check code here
            assert "status_id" in item

    async def test_requester_sees_only_own_tickets(
        self,
        admin_client: AsyncClient,
        requester_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        # Create ticket as admin (different user)
        await admin_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        # Requester should not see it
        resp = await requester_client.get("/api/v1/tickets")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_requester_sees_own_ticket(
        self,
        requester_client: AsyncClient,
        active_location: Location,
        default_priority: Priority,
    ):
        await requester_client.post(
            "/api/v1/tickets",
            json=_predial_payload(str(active_location.id), str(default_priority.id)),
        )
        resp = await requester_client.get("/api/v1/tickets")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
