from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient


async def test_health_database_ok(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert "timestamp" in body


async def test_health_database_unavailable() -> None:
    from app.core.deps import get_db
    from app.main import app

    async def broken_db():
        session = MagicMock()
        session.execute = AsyncMock(side_effect=Exception("Connection refused"))
        yield session

    app.dependency_overrides[get_db] = broken_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "degraded"
        assert body["database"] == "error"
        assert "timestamp" in body
    finally:
        app.dependency_overrides.pop(get_db, None)


async def test_ping(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/ping")

    assert response.status_code == 200
    assert response.json() == {"pong": True}


async def test_unknown_route_returns_404_envelope(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/nonexistent")

    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "NOT_FOUND"
    assert "message" in body
    assert "timestamp" in body
    assert "detail" in body


async def test_unhandled_exception_returns_500_without_leaking_details() -> None:
    import json
    from unittest.mock import MagicMock

    from app.core.exceptions import unhandled_exception_handler

    response = await unhandled_exception_handler(
        MagicMock(), ValueError("super secret internal error")
    )

    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["error"] == "INTERNAL_SERVER_ERROR"
    assert body["message"] == "Um erro interno ocorreu."
    assert "super secret internal error" not in body["message"]
    assert "timestamp" in body
