from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.security import decode_access_token
from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationPreferencesPatch,
    NotificationPreferencesResponse,
    NotificationResponse,
)
from app.modules.notifications.service import NotificationService, build_notification_service
from app.modules.notifications.websocket import handle_ws_connection

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
ws_router = APIRouter(tags=["notifications"])


def _get_redis_url() -> str | None:
    from app.core.config import settings

    url = settings.CELERY_BROKER_URL
    return url if url.startswith("redis") else None


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> NotificationService:
    return build_notification_service(db, current_user.tenant_id, _get_redis_url())


# ── REST Endpoints ────────────────────────────────────────────────────────────


@notifications_router.get("", response_model=NotificationListResponse)
async def list_notifications(
    is_read: bool | None = Query(default=None, description="Filtrar por lidas/não-lidas"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: NotificationService = Depends(_get_service),
    current_user=Depends(get_current_user),
) -> NotificationListResponse:
    return await service.list_for_user(
        current_user.id, is_read=is_read, page=page, page_size=page_size
    )


@notifications_router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: UUID,
    service: NotificationService = Depends(_get_service),
    current_user=Depends(get_current_user),
) -> NotificationResponse:
    return await service.mark_read(notification_id, current_user.id)


@notifications_router.post("/read-all")
async def mark_all_read(
    service: NotificationService = Depends(_get_service),
    current_user=Depends(get_current_user),
) -> dict:
    count = await service.mark_all_read(current_user.id)
    return {"marked_read": count}


@notifications_router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    service: NotificationService = Depends(_get_service),
    current_user=Depends(get_current_user),
) -> NotificationPreferencesResponse:
    return await service.get_preferences(current_user.id)


@notifications_router.patch("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    body: NotificationPreferencesPatch,
    service: NotificationService = Depends(_get_service),
    current_user=Depends(get_current_user),
) -> NotificationPreferencesResponse:
    return await service.update_preferences(current_user.id, body)


# ── WebSocket ─────────────────────────────────────────────────────────────────


@ws_router.websocket("/ws/notifications")
async def ws_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """WebSocket endpoint for real-time notification push.

    Token is validated; connection is dropped on invalid/expired token.
    Uses Redis pub/sub for multi-instance delivery (ADR-0004).
    """
    from jose import JWTError

    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        await websocket.close(code=4001)
        return

    try:
        await handle_ws_connection(websocket, user_id, _get_redis_url())
    except WebSocketDisconnect:
        pass
