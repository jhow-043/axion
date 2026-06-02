from __future__ import annotations

import uuid

from httpx import AsyncClient

from app.modules.tenants.models import Tenant
from app.modules.users.models import User


class TestCreateTeam:
    async def test_admin_creates_team_returns_201(
        self, admin_client: AsyncClient, seeded_tenant: Tenant
    ):
        resp = await admin_client.post(
            "/api/v1/teams", json={"name": "Elétrica", "description": "Equipe elétrica"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Elétrica"
        assert data["description"] == "Equipe elétrica"
        assert data["is_active"] is True
        assert data["tenant_id"] == str(seeded_tenant.id)
        assert data["members"] == []

    async def test_duplicate_name_returns_409(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/teams", json={"name": "Mecânica"})
        resp = await admin_client.post("/api/v1/teams", json={"name": "Mecânica"})
        assert resp.status_code == 409

    async def test_technician_cannot_create_team_returns_403(self, tech_client: AsyncClient):
        resp = await tech_client.post("/api/v1/teams", json={"name": "Automação"})
        assert resp.status_code == 403

    async def test_unauthenticated_returns_401(self, teams_client: AsyncClient):
        resp = await teams_client.post("/api/v1/teams", json={"name": "X"})
        assert resp.status_code == 401


class TestListTeams:
    async def test_admin_lists_teams(self, admin_client: AsyncClient, seeded_tenant: Tenant):
        await admin_client.post("/api/v1/teams", json={"name": "Equipe A"})
        resp = await admin_client.get("/api/v1/teams")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        names = [t["name"] for t in data["items"]]
        assert "Equipe A" in names

    async def test_technician_can_list_teams(self, tech_client: AsyncClient):
        resp = await tech_client.get("/api/v1/teams")
        assert resp.status_code == 200

    async def test_filter_by_is_active(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/teams", json={"name": "Active Team"})
        resp = await admin_client.get("/api/v1/teams?is_active=true")
        assert resp.status_code == 200
        for team in resp.json()["items"]:
            assert team["is_active"] is True


class TestGetTeam:
    async def test_admin_gets_team_detail(self, admin_client: AsyncClient):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "Instrumentação"})
        team_id = create_resp.json()["id"]

        resp = await admin_client.get(f"/api/v1/teams/{team_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == team_id
        assert "members" in data

    async def test_technician_can_get_team(
        self, tech_client: AsyncClient, admin_client: AsyncClient
    ):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "Predial"})
        team_id = create_resp.json()["id"]

        resp = await tech_client.get(f"/api/v1/teams/{team_id}")
        assert resp.status_code == 200

    async def test_unknown_id_returns_404(self, admin_client: AsyncClient):
        resp = await admin_client.get(f"/api/v1/teams/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateTeam:
    async def test_admin_updates_team_name(self, admin_client: AsyncClient):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "Old Name"})
        team_id = create_resp.json()["id"]

        resp = await admin_client.patch(f"/api/v1/teams/{team_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    async def test_duplicate_name_on_update_returns_409(self, admin_client: AsyncClient):
        await admin_client.post("/api/v1/teams", json={"name": "Team Alpha"})
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "Team Beta"})
        team_id = create_resp.json()["id"]

        resp = await admin_client.patch(f"/api/v1/teams/{team_id}", json={"name": "Team Alpha"})
        assert resp.status_code == 409


class TestDeactivateTeam:
    async def test_admin_deactivates_team(self, admin_client: AsyncClient):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "Temp Team"})
        team_id = create_resp.json()["id"]

        resp = await admin_client.post(f"/api/v1/teams/{team_id}/deactivate")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_deactivate_already_inactive_returns_422(self, admin_client: AsyncClient):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "One Time Team"})
        team_id = create_resp.json()["id"]

        await admin_client.post(f"/api/v1/teams/{team_id}/deactivate")
        resp = await admin_client.post(f"/api/v1/teams/{team_id}/deactivate")
        assert resp.status_code == 422


class TestMemberManagement:
    async def test_add_member_returns_member_list(
        self, admin_client: AsyncClient, technician_user: User
    ):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "Team With Member"})
        team_id = create_resp.json()["id"]

        resp = await admin_client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"user_id": str(technician_user.id)},
        )
        assert resp.status_code == 200
        members = resp.json()
        user_ids = [m["user_id"] for m in members]
        assert str(technician_user.id) in user_ids

    async def test_add_inactive_user_returns_422(
        self, admin_client: AsyncClient, inactive_user: User
    ):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "Team X"})
        team_id = create_resp.json()["id"]

        resp = await admin_client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"user_id": str(inactive_user.id)},
        )
        assert resp.status_code == 422

    async def test_add_duplicate_member_returns_409(
        self, admin_client: AsyncClient, technician_user: User
    ):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "No Dupes"})
        team_id = create_resp.json()["id"]

        await admin_client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"user_id": str(technician_user.id)},
        )
        resp = await admin_client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"user_id": str(technician_user.id)},
        )
        assert resp.status_code == 409

    async def test_remove_member_returns_204(
        self, admin_client: AsyncClient, technician_user: User
    ):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "Team Remove"})
        team_id = create_resp.json()["id"]
        await admin_client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"user_id": str(technician_user.id)},
        )

        resp = await admin_client.delete(f"/api/v1/teams/{team_id}/members/{technician_user.id}")
        assert resp.status_code == 204

    async def test_remove_nonexistent_member_returns_404(self, admin_client: AsyncClient):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "Ghost Team"})
        team_id = create_resp.json()["id"]

        resp = await admin_client.delete(f"/api/v1/teams/{team_id}/members/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_list_members_returns_200(
        self, admin_client: AsyncClient, tech_client: AsyncClient, technician_user: User
    ):
        create_resp = await admin_client.post("/api/v1/teams", json={"name": "List Members Team"})
        team_id = create_resp.json()["id"]
        await admin_client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"user_id": str(technician_user.id)},
        )

        resp = await tech_client.get(f"/api/v1/teams/{team_id}/members")
        assert resp.status_code == 200
        assert any(m["user_id"] == str(technician_user.id) for m in resp.json())
