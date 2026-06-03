from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Priority, Status
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.tenants.models import Tenant


class TestCatalogSeed:
    async def test_seed_creates_four_default_priorities(
        self, db_session: AsyncSession, seeded_tenant: Tenant
    ):
        await seed_catalog_defaults(db_session, seeded_tenant.id)
        stmt = select(Priority).where(Priority.tenant_id == seeded_tenant.id)
        result = await db_session.execute(stmt)
        codes = {p.code for p in result.scalars().all()}
        assert codes == {"low", "medium", "high", "critical"}

    async def test_seed_creates_five_default_statuses(
        self, db_session: AsyncSession, seeded_tenant: Tenant
    ):
        await seed_catalog_defaults(db_session, seeded_tenant.id)
        stmt = select(Status).where(Status.tenant_id == seeded_tenant.id)
        result = await db_session.execute(stmt)
        codes = {s.code for s in result.scalars().all()}
        assert codes == {"new", "in_progress", "pending", "resolved", "closed"}

    async def test_seed_is_idempotent(self, db_session: AsyncSession, seeded_tenant: Tenant):
        await seed_catalog_defaults(db_session, seeded_tenant.id)
        await seed_catalog_defaults(db_session, seeded_tenant.id)
        stmt = (
            select(func.count()).select_from(Priority).where(Priority.tenant_id == seeded_tenant.id)
        )
        result = await db_session.execute(stmt)
        assert result.scalar_one() == 4

    async def test_seed_marks_all_as_is_default(
        self, db_session: AsyncSession, seeded_tenant: Tenant
    ):
        await seed_catalog_defaults(db_session, seeded_tenant.id)
        stmt = select(Priority).where(Priority.tenant_id == seeded_tenant.id)
        result = await db_session.execute(stmt)
        assert all(p.is_default for p in result.scalars().all())


class TestPriorities:
    async def test_admin_creates_priority_returns_201(
        self, admin_client: AsyncClient, seeded_tenant: Tenant
    ):
        resp = await admin_client.post(
            "/api/v1/catalog/priorities",
            json={"name": "Urgentíssimo", "code": "emergency", "order": 5},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Urgentíssimo"
        assert data["code"] == "emergency"
        assert data["is_default"] is False
        assert data["tenant_id"] == str(seeded_tenant.id)

    async def test_duplicate_code_returns_409(self, admin_client: AsyncClient):
        await admin_client.post(
            "/api/v1/catalog/priorities", json={"name": "P1", "code": "p1", "order": 10}
        )
        resp = await admin_client.post(
            "/api/v1/catalog/priorities", json={"name": "P2", "code": "p1", "order": 11}
        )
        assert resp.status_code == 409

    async def test_technician_cannot_create_priority_returns_403(self, tech_client: AsyncClient):
        resp = await tech_client.post(
            "/api/v1/catalog/priorities", json={"name": "X", "code": "x", "order": 99}
        )
        assert resp.status_code == 403

    async def test_admin_lists_priorities(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/v1/catalog/priorities")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    async def test_technician_can_list_priorities(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/catalog/priorities")
        assert resp.status_code == 200

    async def test_filter_active_only(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/v1/catalog/priorities?is_active=true")
        assert resp.status_code == 200
        for p in resp.json()["items"]:
            assert p["is_active"] is True

    async def test_admin_updates_priority_name(self, admin_client: AsyncClient):
        cr = await admin_client.post(
            "/api/v1/catalog/priorities", json={"name": "Velha", "code": "old_p", "order": 20}
        )
        pid = cr.json()["id"]
        resp = await admin_client.patch(f"/api/v1/catalog/priorities/{pid}", json={"name": "Nova"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Nova"
        assert resp.json()["code"] == "old_p"

    async def test_admin_deactivates_priority(self, admin_client: AsyncClient):
        cr = await admin_client.post(
            "/api/v1/catalog/priorities", json={"name": "Temp", "code": "tmp_p", "order": 30}
        )
        pid = cr.json()["id"]
        resp = await admin_client.post(f"/api/v1/catalog/priorities/{pid}/deactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_deactivated_priority_excluded_from_active_filter(
        self, admin_client: AsyncClient
    ):
        cr = await admin_client.post(
            "/api/v1/catalog/priorities",
            json={"name": "Inativa", "code": "inact_p", "order": 31},
        )
        pid = cr.json()["id"]
        await admin_client.post(f"/api/v1/catalog/priorities/{pid}/deactivate")
        resp = await admin_client.get("/api/v1/catalog/priorities?is_active=true")
        ids = [p["id"] for p in resp.json()["items"]]
        assert pid not in ids

    async def test_deactivate_already_inactive_returns_422(self, admin_client: AsyncClient):
        cr = await admin_client.post(
            "/api/v1/catalog/priorities", json={"name": "Once", "code": "once_p", "order": 40}
        )
        pid = cr.json()["id"]
        await admin_client.post(f"/api/v1/catalog/priorities/{pid}/deactivate")
        resp = await admin_client.post(f"/api/v1/catalog/priorities/{pid}/deactivate")
        assert resp.status_code == 422

    async def test_unknown_priority_returns_404(self, admin_client: AsyncClient):
        resp = await admin_client.patch(
            f"/api/v1/catalog/priorities/{uuid.uuid4()}", json={"name": "X"}
        )
        assert resp.status_code == 404

    async def test_unauthenticated_returns_401(self, anon_client: AsyncClient):
        resp = await anon_client.get("/api/v1/catalog/priorities")
        assert resp.status_code == 401


class TestStatuses:
    async def test_admin_cannot_create_status_returns_405(self, admin_client: AsyncClient):
        resp = await admin_client.post(
            "/api/v1/catalog/statuses", json={"name": "Custom", "code": "custom"}
        )
        assert resp.status_code == 405

    async def test_admin_lists_statuses(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/v1/catalog/statuses")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    async def test_technician_can_list_statuses(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/catalog/statuses")
        assert resp.status_code == 200

    async def test_patch_status_rejects_behavioral_flags_returns_422(
        self, admin_client: AsyncClient, db_session: AsyncSession, seeded_tenant: Tenant
    ):
        await seed_catalog_defaults(db_session, seeded_tenant.id)
        resp_list = await admin_client.get("/api/v1/catalog/statuses")
        statuses = resp_list.json()["items"]
        assert statuses, "seed must produce statuses"
        sid = statuses[0]["id"]
        resp = await admin_client.patch(
            f"/api/v1/catalog/statuses/{sid}", json={"requires_reason": True}
        )
        assert resp.status_code == 422

    async def test_patch_status_name_succeeds(
        self, admin_client: AsyncClient, db_session: AsyncSession, seeded_tenant: Tenant
    ):
        await seed_catalog_defaults(db_session, seeded_tenant.id)
        resp_list = await admin_client.get("/api/v1/catalog/statuses")
        new_status = next(s for s in resp_list.json()["items"] if s["code"] == "new")
        sid = new_status["id"]
        resp = await admin_client.patch(f"/api/v1/catalog/statuses/{sid}", json={"name": "Aberto"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Aberto"
        assert resp.json()["code"] == "new"

    async def test_unknown_status_returns_404(self, admin_client: AsyncClient):
        resp = await admin_client.patch(
            f"/api/v1/catalog/statuses/{uuid.uuid4()}", json={"name": "X"}
        )
        assert resp.status_code == 404

    async def test_unauthenticated_returns_401(self, anon_client: AsyncClient):
        resp = await anon_client.get("/api/v1/catalog/statuses")
        assert resp.status_code == 401


class TestCategories:
    async def test_admin_creates_category_returns_201(
        self, admin_client: AsyncClient, seeded_tenant: Tenant
    ):
        resp = await admin_client.post(
            "/api/v1/catalog/categories",
            json={"name": "Elétrica", "description": "Problemas elétricos"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Elétrica"
        assert data["tenant_id"] == str(seeded_tenant.id)
        assert data["is_active"] is True

    async def test_duplicate_name_returns_409(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/catalog/categories", json={"name": "Hidráulica"})
        resp = await admin_client.post("/api/v1/catalog/categories", json={"name": "Hidráulica"})
        assert resp.status_code == 409

    async def test_technician_cannot_create_category_returns_403(self, tech_client: AsyncClient):
        resp = await tech_client.post("/api/v1/catalog/categories", json={"name": "XX"})
        assert resp.status_code == 403

    async def test_admin_lists_categories(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/catalog/categories", json={"name": "Civil"})
        resp = await admin_client.get("/api/v1/catalog/categories")
        assert resp.status_code == 200
        assert any(c["name"] == "Civil" for c in resp.json()["items"])

    async def test_technician_can_list_categories(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/catalog/categories")
        assert resp.status_code == 200

    async def test_filter_active_only(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/v1/catalog/categories?is_active=true")
        assert resp.status_code == 200
        for c in resp.json()["items"]:
            assert c["is_active"] is True

    async def test_admin_updates_category(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/catalog/categories", json={"name": "Mecânica"})
        cid = cr.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/catalog/categories/{cid}", json={"name": "Mecânica Industrial"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Mecânica Industrial"

    async def test_duplicate_name_on_update_returns_409(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/catalog/categories", json={"name": "Cat A"})
        cr = await admin_client.post("/api/v1/catalog/categories", json={"name": "Cat B"})
        cid = cr.json()["id"]
        resp = await admin_client.patch(f"/api/v1/catalog/categories/{cid}", json={"name": "Cat A"})
        assert resp.status_code == 409

    async def test_admin_deactivates_category(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/catalog/categories", json={"name": "Temp Cat"})
        cid = cr.json()["id"]
        resp = await admin_client.post(f"/api/v1/catalog/categories/{cid}/deactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_inactive_category_excluded_from_active_filter(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/catalog/categories", json={"name": "Inativa Cat"})
        cid = cr.json()["id"]
        await admin_client.post(f"/api/v1/catalog/categories/{cid}/deactivate")
        resp = await admin_client.get("/api/v1/catalog/categories?is_active=true")
        ids = [c["id"] for c in resp.json()["items"]]
        assert cid not in ids

    async def test_unknown_category_returns_404(self, admin_client: AsyncClient):
        resp = await admin_client.patch(
            f"/api/v1/catalog/categories/{uuid.uuid4()}", json={"name": "Inexistente"}
        )
        assert resp.status_code == 404

    async def test_unauthenticated_returns_401(self, anon_client: AsyncClient):
        resp = await anon_client.get("/api/v1/catalog/categories")
        assert resp.status_code == 401


class TestPendingReasons:
    async def test_admin_creates_pending_reason_returns_201(
        self, admin_client: AsyncClient, seeded_tenant: Tenant
    ):
        resp = await admin_client.post(
            "/api/v1/catalog/pending-reasons",
            json={"name": "Aguardando peça", "description": "Peça em pedido"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Aguardando peça"
        assert data["tenant_id"] == str(seeded_tenant.id)

    async def test_duplicate_name_returns_409(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/catalog/pending-reasons", json={"name": "Duplicado"})
        resp = await admin_client.post(
            "/api/v1/catalog/pending-reasons", json={"name": "Duplicado"}
        )
        assert resp.status_code == 409

    async def test_admin_lists_pending_reasons(self, admin_client: AsyncClient):
        await admin_client.post(
            "/api/v1/catalog/pending-reasons", json={"name": "Aguardando aprovação"}
        )
        resp = await admin_client.get("/api/v1/catalog/pending-reasons")
        assert resp.status_code == 200
        assert any(r["name"] == "Aguardando aprovação" for r in resp.json()["items"])

    async def test_technician_can_list_pending_reasons(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/catalog/pending-reasons")
        assert resp.status_code == 200

    async def test_admin_deactivates_pending_reason(self, admin_client: AsyncClient):
        cr = await admin_client.post(
            "/api/v1/catalog/pending-reasons", json={"name": "Motivo Temp"}
        )
        rid = cr.json()["id"]
        resp = await admin_client.post(f"/api/v1/catalog/pending-reasons/{rid}/deactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_inactive_reason_excluded_from_active_filter(self, admin_client: AsyncClient):
        cr = await admin_client.post(
            "/api/v1/catalog/pending-reasons", json={"name": "Motivo Inativo"}
        )
        rid = cr.json()["id"]
        await admin_client.post(f"/api/v1/catalog/pending-reasons/{rid}/deactivate")
        resp = await admin_client.get("/api/v1/catalog/pending-reasons?is_active=true")
        ids = [r["id"] for r in resp.json()["items"]]
        assert rid not in ids

    async def test_admin_updates_pending_reason(self, admin_client: AsyncClient):
        cr = await admin_client.post(
            "/api/v1/catalog/pending-reasons", json={"name": "Motivo Antigo"}
        )
        rid = cr.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/catalog/pending-reasons/{rid}", json={"name": "Motivo Novo"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Motivo Novo"

    async def test_technician_cannot_create_pending_reason_returns_403(
        self, tech_client: AsyncClient
    ):
        resp = await tech_client.post(
            "/api/v1/catalog/pending-reasons", json={"name": "Não permitido"}
        )
        assert resp.status_code == 403

    async def test_unauthenticated_returns_401(self, anon_client: AsyncClient):
        resp = await anon_client.get("/api/v1/catalog/pending-reasons")
        assert resp.status_code == 401
