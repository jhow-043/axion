"""Tests for app.modules.closures.tasks — Celery auto-close sweep."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.closures.tasks import (
    _auto_close_sweep_async,
    _get_active_tenant_ids,
    auto_close_sweep,
)


# ── helpers ────────────────────────────────────────────────────────────────────


def _session_factory_mock():
    mock_session = AsyncMock()
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=None)
    sessionmaker = MagicMock(return_value=ctx)
    return MagicMock(return_value=sessionmaker), mock_session


# ── _get_active_tenant_ids ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_active_tenant_ids_returns_list():
    t1 = uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [t1]
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=None)
    factory = MagicMock(return_value=MagicMock(return_value=ctx))

    with patch("app.db.session.get_session_factory", factory):
        result = await _get_active_tenant_ids()
    assert t1 in result


# ── auto_close_sweep (sync entry-point) ───────────────────────────────────────


def test_auto_close_sweep_delegates_to_asyncio_run():
    with patch("app.modules.closures.tasks.asyncio.run") as run_mock:
        auto_close_sweep()
    run_mock.assert_called_once()


# ── _auto_close_sweep_async ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_auto_close_sweep_async_no_tenants_is_noop():
    with patch("app.modules.closures.tasks._get_active_tenant_ids", AsyncMock(return_value=[])):
        await _auto_close_sweep_async()


@pytest.mark.asyncio
async def test_auto_close_sweep_async_calls_sweep():
    tenant_id = uuid4()
    factory, mock_session = _session_factory_mock()
    mock_svc = AsyncMock()

    with (
        patch("app.modules.closures.tasks._get_active_tenant_ids", AsyncMock(return_value=[tenant_id])),
        patch("app.db.session.get_session_factory", factory),
        patch("app.modules.closures.service.ClosureService", MagicMock(return_value=mock_svc)),
        patch("app.modules.closures.repository.ValidationRepository", MagicMock()),
        patch("app.modules.closures.repository.TenantSettingsRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketRepository", MagicMock()),
        patch("app.modules.tickets.repository.SolutionRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketObserverRepository", MagicMock()),
        patch("app.modules.catalog.repository.StatusRepository", MagicMock()),
        patch("app.modules.users.repository.UserRepository", MagicMock()),
        patch("app.modules.timeline.repository.TicketEventRepository", MagicMock()),
        patch("app.modules.timeline.service.TimelineService", MagicMock()),
        patch("app.modules.notifications.service.build_notification_service", MagicMock()),
    ):
        await _auto_close_sweep_async()

    mock_svc.sweep_auto_close.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_auto_close_sweep_async_rolls_back_on_error():
    tenant_id = uuid4()
    factory, mock_session = _session_factory_mock()
    mock_svc = AsyncMock()
    mock_svc.sweep_auto_close.side_effect = RuntimeError("fail")

    with (
        patch("app.modules.closures.tasks._get_active_tenant_ids", AsyncMock(return_value=[tenant_id])),
        patch("app.db.session.get_session_factory", factory),
        patch("app.modules.closures.service.ClosureService", MagicMock(return_value=mock_svc)),
        patch("app.modules.closures.repository.ValidationRepository", MagicMock()),
        patch("app.modules.closures.repository.TenantSettingsRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketRepository", MagicMock()),
        patch("app.modules.tickets.repository.SolutionRepository", MagicMock()),
        patch("app.modules.tickets.repository.TicketObserverRepository", MagicMock()),
        patch("app.modules.catalog.repository.StatusRepository", MagicMock()),
        patch("app.modules.users.repository.UserRepository", MagicMock()),
        patch("app.modules.timeline.repository.TicketEventRepository", MagicMock()),
        patch("app.modules.timeline.service.TimelineService", MagicMock()),
        patch("app.modules.notifications.service.build_notification_service", MagicMock()),
    ):
        await _auto_close_sweep_async()  # must not raise

    mock_session.rollback.assert_awaited_once()
    mock_session.commit.assert_not_awaited()
