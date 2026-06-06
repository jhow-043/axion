from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import ADMIN_CONFIG
from app.modules.audit.schemas import AuditLogListResponse
from app.modules.audit.service import AuditService, build_audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AuditService:
    return build_audit_service(db, current_user.tenant_id)


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    actor_id: UUID | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: AuditService = Depends(_get_service),
    _: None = Depends(require_permission(ADMIN_CONFIG)),
) -> AuditLogListResponse:
    return await service.list_logs(
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
