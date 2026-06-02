from __future__ import annotations

import uuid

from httpx import AsyncClient

from app.modules.tenants.models import Tenant


class TestCreateSector:
    async def test_admin_creates_sector_returns_201(
        self, admin_client: AsyncClient, seeded_tenant: Tenant
    ):
        resp = await admin_client.post(
            "/api/v1/sectors", json={"name": "TI", "description": "Tecnologia"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "TI"
        assert data["description"] == "Tecnologia"
        assert data["is_active"] is True
        assert data["tenant_id"] == str(seeded_tenant.id)

    async def test_duplicate_name_returns_409(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/sectors", json={"name": "Mecânica"})
        resp = await admin_client.post("/api/v1/sectors", json={"name": "Mecânica"})
        assert resp.status_code == 409

    async def test_technician_cannot_create_sector_returns_403(self, tech_client: AsyncClient):
        resp = await tech_client.post("/api/v1/sectors", json={"name": "Civil"})
        assert resp.status_code == 403

    async def test_unauthenticated_returns_401(self, anon_client: AsyncClient):
        resp = await anon_client.post("/api/v1/sectors", json={"name": "X"})
        assert resp.status_code == 401


class TestListSectors:
    async def test_admin_lists_sectors(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/sectors", json={"name": "Elétrica"})
        resp = await admin_client.get("/api/v1/sectors")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert any(s["name"] == "Elétrica" for s in data["items"])

    async def test_technician_can_list_sectors(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/sectors")
        assert resp.status_code == 200

    async def test_filter_by_is_active_true(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/sectors", json={"name": "Ativo"})
        resp = await admin_client.get("/api/v1/sectors?is_active=true")
        assert resp.status_code == 200
        for s in resp.json()["items"]:
            assert s["is_active"] is True

    async def test_pagination_fields_present(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/v1/sectors")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data


class TestGetSector:
    async def test_admin_gets_sector(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/sectors", json={"name": "Instrumentação"})
        sector_id = cr.json()["id"]
        resp = await admin_client.get(f"/api/v1/sectors/{sector_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sector_id

    async def test_unknown_id_returns_404(self, admin_client: AsyncClient):
        resp = await admin_client.get(f"/api/v1/sectors/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateSector:
    async def test_admin_updates_name(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/sectors", json={"name": "Old Sector"})
        sector_id = cr.json()["id"]
        resp = await admin_client.patch(f"/api/v1/sectors/{sector_id}", json={"name": "New Sector"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Sector"

    async def test_duplicate_name_on_update_returns_409(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/sectors", json={"name": "Alpha"})
        cr = await admin_client.post("/api/v1/sectors", json={"name": "Beta"})
        sector_id = cr.json()["id"]
        resp = await admin_client.patch(f"/api/v1/sectors/{sector_id}", json={"name": "Alpha"})
        assert resp.status_code == 409


class TestDeactivateSector:
    async def test_admin_deactivates_sector(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/sectors", json={"name": "Temp Sector"})
        sector_id = cr.json()["id"]
        resp = await admin_client.post(f"/api/v1/sectors/{sector_id}/deactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_deactivate_already_inactive_returns_422(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/sectors", json={"name": "One Time"})
        sector_id = cr.json()["id"]
        await admin_client.post(f"/api/v1/sectors/{sector_id}/deactivate")
        resp = await admin_client.post(f"/api/v1/sectors/{sector_id}/deactivate")
        assert resp.status_code == 422

    async def test_inactive_sector_not_in_active_filter(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/sectors", json={"name": "Inactive One"})
        sector_id = cr.json()["id"]
        await admin_client.post(f"/api/v1/sectors/{sector_id}/deactivate")
        resp = await admin_client.get("/api/v1/sectors?is_active=true")
        ids = [s["id"] for s in resp.json()["items"]]
        assert sector_id not in ids

    async def test_reactivate_restores_sector(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/sectors", json={"name": "Dormant"})
        sector_id = cr.json()["id"]
        await admin_client.post(f"/api/v1/sectors/{sector_id}/deactivate")
        resp = await admin_client.post(f"/api/v1/sectors/{sector_id}/reactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True


class TestCreateLocation:
    async def test_admin_creates_location_returns_201(
        self, admin_client: AsyncClient, seeded_tenant: Tenant
    ):
        resp = await admin_client.post(
            "/api/v1/locations", json={"name": "Galpão Principal", "description": "Área industrial"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Galpão Principal"
        assert data["description"] == "Área industrial"
        assert data["is_active"] is True
        assert data["tenant_id"] == str(seeded_tenant.id)

    async def test_duplicate_name_returns_409(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/locations", json={"name": "Sala 101"})
        resp = await admin_client.post("/api/v1/locations", json={"name": "Sala 101"})
        assert resp.status_code == 409

    async def test_technician_cannot_create_location_returns_403(self, tech_client: AsyncClient):
        resp = await tech_client.post("/api/v1/locations", json={"name": "Almoxarifado"})
        assert resp.status_code == 403

    async def test_unauthenticated_returns_401(self, anon_client: AsyncClient):
        resp = await anon_client.post("/api/v1/locations", json={"name": "X"})
        assert resp.status_code == 401


class TestListLocations:
    async def test_admin_lists_locations(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/locations", json={"name": "Refeitório"})
        resp = await admin_client.get("/api/v1/locations")
        assert resp.status_code == 200
        assert any(loc["name"] == "Refeitório" for loc in resp.json()["items"])

    async def test_technician_can_list_locations(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/locations")
        assert resp.status_code == 200

    async def test_filter_active_only(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/v1/locations?is_active=true")
        assert resp.status_code == 200
        for loc in resp.json()["items"]:
            assert loc["is_active"] is True


class TestGetLocation:
    async def test_admin_gets_location(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/locations", json={"name": "Portaria"})
        loc_id = cr.json()["id"]
        resp = await admin_client.get(f"/api/v1/locations/{loc_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == loc_id

    async def test_unknown_id_returns_404(self, admin_client: AsyncClient):
        resp = await admin_client.get(f"/api/v1/locations/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateLocation:
    async def test_admin_updates_location(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/locations", json={"name": "Bloco A"})
        loc_id = cr.json()["id"]
        resp = await admin_client.patch(f"/api/v1/locations/{loc_id}", json={"name": "Bloco B"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Bloco B"

    async def test_duplicate_name_on_update_returns_409(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/locations", json={"name": "Dep A"})
        cr = await admin_client.post("/api/v1/locations", json={"name": "Dep B"})
        loc_id = cr.json()["id"]
        resp = await admin_client.patch(f"/api/v1/locations/{loc_id}", json={"name": "Dep A"})
        assert resp.status_code == 409


class TestDeactivateLocation:
    async def test_admin_deactivates_location(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/locations", json={"name": "Temp Local"})
        loc_id = cr.json()["id"]
        resp = await admin_client.post(f"/api/v1/locations/{loc_id}/deactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_deactivate_already_inactive_returns_422(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/locations", json={"name": "One Shot"})
        loc_id = cr.json()["id"]
        await admin_client.post(f"/api/v1/locations/{loc_id}/deactivate")
        resp = await admin_client.post(f"/api/v1/locations/{loc_id}/deactivate")
        assert resp.status_code == 422

    async def test_inactive_location_not_in_active_filter(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/locations", json={"name": "Inactive Loc"})
        loc_id = cr.json()["id"]
        await admin_client.post(f"/api/v1/locations/{loc_id}/deactivate")
        resp = await admin_client.get("/api/v1/locations?is_active=true")
        ids = [loc["id"] for loc in resp.json()["items"]]
        assert loc_id not in ids

    async def test_reactivate_restores_location(self, admin_client: AsyncClient):
        cr = await admin_client.post("/api/v1/locations", json={"name": "Dormant Loc"})
        loc_id = cr.json()["id"]
        await admin_client.post(f"/api/v1/locations/{loc_id}/deactivate")
        resp = await admin_client.post(f"/api/v1/locations/{loc_id}/reactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True
