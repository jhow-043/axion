"""Tests for app.modules.notifications.websocket — pub/sub and WS helpers."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.modules.notifications import websocket as ws_module
from app.modules.notifications.websocket import (
    _remove_local,
    _wait_for_disconnect,
    handle_ws_connection,
    publish_to_user,
)

# ── _remove_local ──────────────────────────────────────────────────────────────


def test_remove_local_removes_existing():
    uid = str(uuid4())
    mock_ws = MagicMock()
    ws_module._local_connections[uid] = [mock_ws]

    _remove_local(uid, mock_ws)

    assert uid not in ws_module._local_connections


def test_remove_local_noop_when_not_present():
    uid = str(uuid4())
    mock_ws = MagicMock()

    _remove_local(uid, mock_ws)  # must not raise


def test_remove_local_leaves_other_connections():
    uid = str(uuid4())
    ws_a, ws_b = MagicMock(), MagicMock()
    ws_module._local_connections[uid] = [ws_a, ws_b]

    _remove_local(uid, ws_a)

    assert ws_b in ws_module._local_connections[uid]


# ── publish_to_user (local fallback) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_publish_to_user_local_fallback_sends():
    user_id = uuid4()
    uid = str(user_id)
    mock_ws = AsyncMock()
    ws_module._local_connections[uid] = [mock_ws]

    await publish_to_user(user_id, {"type": "test"})

    mock_ws.send_text.assert_awaited_once()
    ws_module._local_connections.pop(uid, None)


@pytest.mark.asyncio
async def test_publish_to_user_removes_dead_connection():
    user_id = uuid4()
    uid = str(user_id)
    dead_ws = AsyncMock()
    dead_ws.send_text.side_effect = Exception("disconnected")
    ws_module._local_connections[uid] = [dead_ws]

    await publish_to_user(user_id, {"type": "ping"})

    assert uid not in ws_module._local_connections


@pytest.mark.asyncio
async def test_publish_to_user_no_connections_is_noop():
    user_id = uuid4()
    uid = str(user_id)
    ws_module._local_connections.pop(uid, None)

    await publish_to_user(user_id, {"event": "x"})  # must not raise


@pytest.mark.asyncio
async def test_publish_to_user_redis_fallback_on_redis_error():
    """Falls back to local delivery when Redis publish fails."""
    user_id = uuid4()
    uid = str(user_id)
    mock_ws = AsyncMock()
    ws_module._local_connections[uid] = [mock_ws]

    mock_redis = AsyncMock()
    mock_redis.publish.side_effect = Exception("redis down")

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        await publish_to_user(user_id, {"type": "x"}, redis_url="redis://localhost:6379")

    mock_ws.send_text.assert_awaited_once()
    ws_module._local_connections.pop(uid, None)


# ── _wait_for_disconnect ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_wait_for_disconnect_exits_on_disconnect_message():
    mock_ws = AsyncMock()
    mock_ws.receive = AsyncMock(side_effect=[
        {"type": "websocket.receive", "text": "ping"},
        {"type": "websocket.disconnect"},
    ])

    await _wait_for_disconnect(mock_ws)

    assert mock_ws.receive.await_count == 2


@pytest.mark.asyncio
async def test_wait_for_disconnect_exits_on_exception():
    mock_ws = AsyncMock()
    mock_ws.receive = AsyncMock(side_effect=RuntimeError("closed"))

    await _wait_for_disconnect(mock_ws)  # must not raise


# ── handle_ws_connection (local, no Redis) ────────────────────────────────────


@pytest.mark.asyncio
async def test_handle_ws_connection_local_path():
    user_id = uuid4()
    mock_ws = AsyncMock()
    mock_ws.receive = AsyncMock(side_effect=[{"type": "websocket.disconnect"}])

    await handle_ws_connection(mock_ws, user_id)

    mock_ws.accept.assert_awaited_once()
    uid = str(user_id)
    assert uid not in ws_module._local_connections


@pytest.mark.asyncio
async def test_handle_ws_connection_cleans_up_on_error():
    user_id = uuid4()
    mock_ws = AsyncMock()
    mock_ws.receive = AsyncMock(side_effect=RuntimeError("boom"))

    await handle_ws_connection(mock_ws, user_id)

    uid = str(user_id)
    assert uid not in ws_module._local_connections
