"""Integration tests for reports endpoints (P16 — relatorios).
The reports module uses DashboardRepository. Detailed report data tests live in
tests/dashboards/test_integration.py. These tests cover HTTP surface and permissions.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reports_tickets_requires_auth(async_client: AsyncClient):
    resp = await async_client.get(
        "/api/v1/reports/tickets",
        params={"date_from": "2026-01-01T00:00:00", "date_to": "2026-01-31T00:00:00"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_reports_sla_requires_auth(async_client: AsyncClient):
    resp = await async_client.get(
        "/api/v1/reports/sla",
        params={"date_from": "2026-01-01T00:00:00", "date_to": "2026-01-31T00:00:00"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_reports_equipments_requires_auth(async_client: AsyncClient):
    resp = await async_client.get(
        "/api/v1/reports/equipments",
        params={"date_from": "2026-01-01T00:00:00", "date_to": "2026-01-31T00:00:00"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_reports_teams_requires_auth(async_client: AsyncClient):
    resp = await async_client.get(
        "/api/v1/reports/teams",
        params={"date_from": "2026-01-01T00:00:00", "date_to": "2026-01-31T00:00:00"},
    )
    assert resp.status_code == 401
