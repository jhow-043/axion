"""Tests for app.modules.sla.tasks — Celery sweep entry-points."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.sla.tasks import (
    _alert_sweep_async,
    _breach_sweep_async,
    _get_active_tenant_ids,
    alert_sweep,
    breach_sweep,
)


# ── helpers ────────────────────────────────────────────────────────────────────


def _session_factory_mock():
    """Returns (get_session_factory mock, inner session mock)."""
    mock_session = AsyncMock()
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=None)
    sessionmaker = MagicMock(return_value=ctx)
    return MagicMock(return_value=sessionmaker), mock_session


# ── _get_active_tenant_ids ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_active_tenant_ids_returns_empty_when_no_tenants():
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=None)
    sessionmaker = MagicMock(return_value=ctx)
    factory = MagicMock(return_value=sessionmaker)

    with patch("app.db.session.get_session_factory", factory):
        result = await _get_active_tenant_ids()
    assert result == []


@pytest.mark.asyncio
async def test_get_active_tenant_ids_returns_ids():
    t1, t2 = uuid4(), uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [t1, t2]
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=None)
    sessionmaker = MagicMock(return_value=ctx)
    factory = MagicMock(return_value=sessionmaker)

    with patch("app.db.session.get_session_factory", factory):
        result = await _get_active_tenant_ids()
    assert t1 in result and t2 in result


# ── breach_sweep / alert_sweep (sync entry-points) ────────────────────────────


def test_breach_sweep_delegates_to_asyncio_run():
    with patch("app.modules.sla.tasks.asyncio.run") as run_mock:
        breach_sweep()
    run_mock.assert_called_once()


def test_alert_sweep_delegates_to_asyncio_run():
    with patch("app.modules.sla.tasks.asyncio.run") as run_mock:
        alert_sweep()
    run_mock.assert_called_once()


# ── _breach_sweep_async ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_breach_sweep_async_no_tenants_is_noop():
    with patch("app.modules.sla.tasks._get_active_tenant_ids", AsyncMock(return_value=[])):
        await _breach_sweep_async()


@pytest.mark.asyncio
async def test_breach_sweep_async_calls_sweep_breaches():
    tenant_id = uuid4()
    factory, mock_session = _session_factory_mock()
    mock_svc = AsyncMock()

    with (
        patch("app.modules.sla.tasks._get_active_tenant_ids", AsyncMock(return_value=[tenant_id])),
        patch("app.db.session.get_session_factory", factory),
        patch("app.modules.sla.service.SlaService", MagicMock(return_value=mock_svc)),
        patch("app.modules.sla.repository.SlaPolicyRepository", MagicMock()),
        patch("app.modules.sla.repository.SlaTrackerRepository", MagicMock()),
        patch("app.modules.sla.repository.SlaPauseRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketObserverRepository", MagicMock()),
        patch("app.modules.timeline.repository.TicketEventRepository", MagicMock()),
        patch("app.modules.timeline.service.TimelineService", MagicMock()),
        patch("app.modules.users.repository.UserRepository", MagicMock()),
        patch("app.modules.notifications.service.build_notification_service", MagicMock()),
    ):
        await _breach_sweep_async()

    mock_svc.sweep_breaches.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_breach_sweep_async_rolls_back_on_error():
    tenant_id = uuid4()
    factory, mock_session = _session_factory_mock()
    mock_svc = AsyncMock()
    mock_svc.sweep_breaches.side_effect = RuntimeError("db error")

    with (
        patch("app.modules.sla.tasks._get_active_tenant_ids", AsyncMock(return_value=[tenant_id])),
        patch("app.db.session.get_session_factory", factory),
        patch("app.modules.sla.service.SlaService", MagicMock(return_value=mock_svc)),
        patch("app.modules.sla.repository.SlaPolicyRepository", MagicMock()),
        patch("app.modules.sla.repository.SlaTrackerRepository", MagicMock()),
        patch("app.modules.sla.repository.SlaPauseRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketObserverRepository", MagicMock()),
        patch("app.modules.timeline.repository.TicketEventRepository", MagicMock()),
        patch("app.modules.timeline.service.TimelineService", MagicMock()),
        patch("app.modules.users.repository.UserRepository", MagicMock()),
        patch("app.modules.notifications.service.build_notification_service", MagicMock()),
    ):
        await _breach_sweep_async()  # must not raise

    mock_session.rollback.assert_awaited_once()
    mock_session.commit.assert_not_awaited()


# ── _alert_sweep_async ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_alert_sweep_async_no_tenants_is_noop():
    with patch("app.modules.sla.tasks._get_active_tenant_ids", AsyncMock(return_value=[])):
        await _alert_sweep_async()


@pytest.mark.asyncio
async def test_alert_sweep_async_calls_sweep_alerts():
    tenant_id = uuid4()
    factory, mock_session = _session_factory_mock()
    mock_svc = AsyncMock()

    with (
        patch("app.modules.sla.tasks._get_active_tenant_ids", AsyncMock(return_value=[tenant_id])),
        patch("app.db.session.get_session_factory", factory),
        patch("app.modules.sla.service.SlaService", MagicMock(return_value=mock_svc)),
        patch("app.modules.sla.repository.SlaPolicyRepository", MagicMock()),
        patch("app.modules.sla.repository.SlaTrackerRepository", MagicMock()),
        patch("app.modules.sla.repository.SlaPauseRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketRepository", MagicMock()),
        patch("app.modules.notifications.service.build_notification_service", MagicMock()),
    ):
        await _alert_sweep_async()

    mock_svc.sweep_alerts.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_alert_sweep_async_rolls_back_on_error():
    tenant_id = uuid4()
    factory, mock_session = _session_factory_mock()
    mock_svc = AsyncMock()
    mock_svc.sweep_alerts.side_effect = RuntimeError("boom")

    with (
        patch("app.modules.sla.tasks._get_active_tenant_ids", AsyncMock(return_value=[tenant_id])),
        patch("app.db.session.get_session_factory", factory),
        patch("app.modules.sla.service.SlaService", MagicMock(return_value=mock_svc)),
        patch("app.modules.sla.repository.SlaPolicyRepository", MagicMock()),
        patch("app.modules.sla.repository.SlaTrackerRepository", MagicMock()),
        patch("app.modules.sla.repository.SlaPauseRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketRepository", MagicMock()),
        patch("app.modules.notifications.service.build_notification_service", MagicMock()),
    ):
        await _alert_sweep_async()  # must not raise

    mock_session.rollback.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
