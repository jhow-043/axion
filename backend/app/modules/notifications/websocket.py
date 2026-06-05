from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Per-process registry for local push (fallback when Redis pub/sub is unavailable)
_local_connections: dict[str, list[WebSocket]] = {}


async def publish_to_user(user_id: UUID, data: dict, redis_url: str | None = None) -> None:
    """Publish a real-time notification to a user.

    Uses Redis pub/sub when available (multi-instance support, ADR-0004 pattern).
    Falls back to in-process delivery for single-instance deployments.
    """
    payload = json.dumps(data)
    if redis_url:
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(redis_url)
            await client.publish(f"notifications:{user_id}", payload)
            await client.aclose()
            return
        except Exception:
            logger.warning("Redis publish failed for user %s; falling back to local push", user_id)

    # Local fallback — works only within the same process
    uid = str(user_id)
    dead: list[WebSocket] = []
    for ws in list(_local_connections.get(uid, [])):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _remove_local(uid, ws)


async def handle_ws_connection(
    ws: WebSocket,
    user_id: UUID,
    redis_url: str | None = None,
) -> None:
    """Accept and drive a WebSocket connection for a single authenticated user.

    Subscribes to Redis pub/sub channel for multi-instance push (spec RN-04).
    Falls back to in-process delivery when Redis is unavailable.
    Blocks until the client disconnects.
    """
    await ws.accept()
    uid = str(user_id)
    _local_connections.setdefault(uid, []).append(ws)

    try:
        if redis_url:
            await _handle_with_redis(ws, user_id, redis_url)
        else:
            await _wait_for_disconnect(ws)
    finally:
        _remove_local(uid, ws)


async def _handle_with_redis(ws: WebSocket, user_id: UUID, redis_url: str) -> None:
    try:
        import redis.asyncio as aioredis
    except ImportError:
        await _wait_for_disconnect(ws)
        return

    channel = f"notifications:{user_id}"
    client = aioredis.from_url(redis_url)
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)

    async def redis_reader() -> None:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    await ws.send_text(message["data"].decode())
                except Exception:
                    return

    reader_task = asyncio.create_task(redis_reader())
    try:
        await _wait_for_disconnect(ws)
    finally:
        reader_task.cancel()
        try:
            await reader_task
        except asyncio.CancelledError:
            pass
        await pubsub.unsubscribe(channel)
        await client.aclose()


async def _wait_for_disconnect(ws: WebSocket) -> None:
    try:
        while True:
            data = await ws.receive()
            if data.get("type") == "websocket.disconnect":
                break
    except Exception:
        pass


def _remove_local(uid: str, ws: WebSocket) -> None:
    conns = _local_connections.get(uid, [])
    if ws in conns:
        conns.remove(ws)
    if not conns:
        _local_connections.pop(uid, None)
