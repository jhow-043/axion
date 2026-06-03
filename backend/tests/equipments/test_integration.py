from __future__ import annotations

import uuid

from httpx import AsyncClient

from app.modules.locations.models import Sector
from app.modules.tenants.models import Tenant


def _equipment_payload(sector_id: str, code: str | None = None) -> dict:
    return {
        "code": code or f"EQ-{uuid.uuid4().hex[:6].upper()}",
        "name": "Motor Elétrico 10cv",
        "sector_id": sector_id,
        "manufacturer": "WEG",
        "model": "W22",
        "serial_number": "SN-12345",
        "notes": "Motor principal da linha A",
    }


class TestCreateEquipment:
    async def test_admin_creates_equipment_returns_201(
        self,
        admin_client: AsyncClient,
        seeded_tenant: Tenant,
        active_sector: Sector,
    ):
        resp = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Motor Elétrico 10cv"
        assert data["manufacturer"] == "WEG"
        assert data["model"] == "W22"
        assert data["serial_number"] == "SN-12345"
        assert data["is_active"] is True
        assert data["tenant_id"] == str(seeded_tenant.id)
        assert data["sector_id"] == str(active_sector.id)

    async def test_duplicate_code_returns_409(
        self, admin_client: AsyncClient, active_sector: Sector
    ):
        payload = _equipment_payload(str(active_sector.id), code="EQ-DUP")
        await admin_client.post("/api/v1/equipments", json=payload)
        resp = await admin_client.post("/api/v1/equipments", json=payload)
        assert resp.status_code == 409

    async def test_inactive_sector_returns_422(
        self, admin_client: AsyncClient, inactive_sector: Sector
    ):
        resp = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(inactive_sector.id))
        )
        assert resp.status_code == 422

    async def test_unknown_sector_returns_404(self, admin_client: AsyncClient):
        resp = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(uuid.uuid4()))
        )
        assert resp.status_code == 404

    async def test_technician_cannot_create_returns_403(
        self, tech_client: AsyncClient, active_sector: Sector
    ):
        resp = await tech_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        assert resp.status_code == 403

    async def test_unauthenticated_returns_401(
        self, anon_client: AsyncClient, active_sector: Sector
    ):
        resp = await anon_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        assert resp.status_code == 401


class TestListEquipments:
    async def test_admin_lists_equipments(self, admin_client: AsyncClient, active_sector: Sector):
        await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        resp = await admin_client.get("/api/v1/equipments")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 1

    async def test_technician_can_list(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/equipments")
        assert resp.status_code == 200

    async def test_filter_by_sector_id(self, admin_client: AsyncClient, active_sector: Sector):
        await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        resp = await admin_client.get(f"/api/v1/equipments?sector_id={active_sector.id}")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["sector_id"] == str(active_sector.id)

    async def test_filter_by_is_active(self, admin_client: AsyncClient, active_sector: Sector):
        await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        resp = await admin_client.get("/api/v1/equipments?is_active=true")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["is_active"] is True

    async def test_search_by_name(self, admin_client: AsyncClient, active_sector: Sector):
        payload = _equipment_payload(str(active_sector.id))
        payload["name"] = "Bomba Hidráulica Especial"
        await admin_client.post("/api/v1/equipments", json=payload)
        resp = await admin_client.get("/api/v1/equipments?search=Hidráulica")
        assert resp.status_code == 200
        assert any("Hidráulica" in i["name"] for i in resp.json()["items"])

    async def test_pagination_fields_present(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/v1/equipments")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data


class TestGetEquipment:
    async def test_get_returns_equipment(self, admin_client: AsyncClient, active_sector: Sector):
        cr = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        eid = cr.json()["id"]
        resp = await admin_client.get(f"/api/v1/equipments/{eid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == eid

    async def test_unknown_id_returns_404(self, admin_client: AsyncClient):
        resp = await admin_client.get(f"/api/v1/equipments/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateEquipment:
    async def test_patch_name_and_manufacturer(
        self, admin_client: AsyncClient, active_sector: Sector
    ):
        cr = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        eid = cr.json()["id"]
        resp = await admin_client.patch(
            f"/api/v1/equipments/{eid}", json={"name": "Novo Nome", "manufacturer": "ABB"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Novo Nome"
        assert data["manufacturer"] == "ABB"

    async def test_technician_cannot_patch_returns_403(
        self, admin_client: AsyncClient, tech_client: AsyncClient, active_sector: Sector
    ):
        cr = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        eid = cr.json()["id"]
        resp = await tech_client.patch(f"/api/v1/equipments/{eid}", json={"name": "X"})
        assert resp.status_code == 403


class TestDeactivateActivate:
    async def test_deactivate_sets_is_active_false(
        self, admin_client: AsyncClient, active_sector: Sector
    ):
        cr = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        eid = cr.json()["id"]
        resp = await admin_client.post(f"/api/v1/equipments/{eid}/deactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_activate_sets_is_active_true(
        self, admin_client: AsyncClient, active_sector: Sector
    ):
        cr = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        eid = cr.json()["id"]
        await admin_client.post(f"/api/v1/equipments/{eid}/deactivate")
        resp = await admin_client.post(f"/api/v1/equipments/{eid}/activate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    async def test_deactivate_already_inactive_returns_422(
        self, admin_client: AsyncClient, active_sector: Sector
    ):
        cr = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        eid = cr.json()["id"]
        await admin_client.post(f"/api/v1/equipments/{eid}/deactivate")
        resp = await admin_client.post(f"/api/v1/equipments/{eid}/deactivate")
        assert resp.status_code == 422

    async def test_activate_already_active_returns_422(
        self, admin_client: AsyncClient, active_sector: Sector
    ):
        cr = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        eid = cr.json()["id"]
        resp = await admin_client.post(f"/api/v1/equipments/{eid}/activate")
        assert resp.status_code == 422


class TestEquipmentTickets:
    async def test_get_tickets_returns_empty_list(
        self, admin_client: AsyncClient, active_sector: Sector
    ):
        cr = await admin_client.post(
            "/api/v1/equipments", json=_equipment_payload(str(active_sector.id))
        )
        eid = cr.json()["id"]
        resp = await admin_client.get(f"/api/v1/equipments/{eid}/tickets")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_get_tickets_unknown_equipment_returns_404(self, admin_client: AsyncClient):
        resp = await admin_client.get(f"/api/v1/equipments/{uuid.uuid4()}/tickets")
        assert resp.status_code == 404
