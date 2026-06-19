from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_module, require_permission
from app.core.permissions import ADMIN_CONFIG, TICKET_READ, TICKET_VALIDATE
from app.modules.catalog.repository import StatusRepository
from app.modules.closures.repository import TenantSettingsRepository, ValidationRepository
from app.modules.closures.schemas import (
    TenantSettingsPatch,
    TenantSettingsResponse,
    ValidationReject,
    ValidationResponse,
)
from app.modules.closures.service import ClosureService
from app.modules.notifications.service import build_notification_service
from app.modules.tickets.repository import (
    SolutionRepository,
    TicketObserverRepository,
    TicketRepository,
)
from app.modules.timeline.repository import TicketEventRepository
from app.modules.timeline.service import TimelineService
from app.modules.users.repository import UserRepository

tickets_closures_router = APIRouter(
    prefix="/tickets",
    tags=["closures"],
    dependencies=[Depends(require_module("manutencao"))],
)
admin_router = APIRouter(
    prefix="/admin",
    tags=["closures"],
    dependencies=[Depends(require_module("manutencao"))],
)


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ClosureService:
    tid = current_user.tenant_id
    return ClosureService(
        validation_repo=ValidationRepository(db, tid),
        settings_repo=TenantSettingsRepository(db, tid),
        ticket_repo=TicketRepository(db, tid),
        solution_repo=SolutionRepository(db, tid),
        status_repo=StatusRepository(db, tid),
        user_repo=UserRepository(db, tid),
        timeline_svc=TimelineService(
            event_repo=TicketEventRepository(db, tid),
            ticket_repo=TicketRepository(db, tid),
            observer_repo=TicketObserverRepository(db, tid),
            user_repo=UserRepository(db, tid),
        ),
        notification_svc=build_notification_service(db, tid),
    )


@tickets_closures_router.get("/{ticket_id}/validation", response_model=ValidationResponse)
async def get_validation(
    ticket_id: UUID,
    service: ClosureService = Depends(_get_service),
    _: None = Depends(require_permission(TICKET_READ)),
) -> ValidationResponse:
    return await service.get_validation(ticket_id)


@tickets_closures_router.post("/{ticket_id}/validation/approve", response_model=ValidationResponse)
async def approve_validation(
    ticket_id: UUID,
    service: ClosureService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_VALIDATE)),
) -> ValidationResponse:
    return await service.approve(ticket_id, actor_id=current_user.id)


@tickets_closures_router.post("/{ticket_id}/validation/reject", response_model=ValidationResponse)
async def reject_validation(
    ticket_id: UUID,
    body: ValidationReject,
    service: ClosureService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_VALIDATE)),
) -> ValidationResponse:
    return await service.reject(ticket_id, body, actor_id=current_user.id)


@admin_router.get("/settings", response_model=TenantSettingsResponse)
async def get_settings(
    service: ClosureService = Depends(_get_service),
    _: None = Depends(require_permission(ADMIN_CONFIG)),
) -> TenantSettingsResponse:
    return await service.get_settings()


@admin_router.patch("/settings", response_model=TenantSettingsResponse)
async def update_settings(
    body: TenantSettingsPatch,
    service: ClosureService = Depends(_get_service),
    current_user=Depends(require_permission(ADMIN_CONFIG)),
) -> TenantSettingsResponse:
    return await service.update_settings(body, actor_id=current_user.id)
