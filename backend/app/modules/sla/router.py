from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import ADMIN_CONFIG, TICKET_READ
from app.modules.notifications.service import NotificationService
from app.modules.sla.repository import SlaPauseRepository, SlaPolicyRepository, SlaTrackerRepository
from app.modules.sla.schemas import (
    SlaPolicyCreate,
    SlaPolicyListResponse,
    SlaPolicyPatch,
    SlaPolicyResponse,
    SlaTicketResponse,
)
from app.modules.sla.service import SlaService
from app.modules.tickets.repository import TicketRepository

sla_router = APIRouter(prefix="/sla", tags=["sla"])
tickets_sla_router = APIRouter(prefix="/tickets", tags=["sla"])


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SlaService:
    tid = current_user.tenant_id
    return SlaService(
        policy_repo=SlaPolicyRepository(db, tid),
        tracker_repo=SlaTrackerRepository(db, tid),
        pause_repo=SlaPauseRepository(db, tid),
        ticket_repo=TicketRepository(db, tid),
        notification_svc=NotificationService(),
    )


# ── Políticas ─────────────────────────────────────────────────────────────────

@sla_router.get("/policies", response_model=SlaPolicyListResponse)
async def list_policies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: SlaService = Depends(_get_service),
    _: None = Depends(require_permission(ADMIN_CONFIG)),
) -> SlaPolicyListResponse:
    return await service.list_policies(page=page, page_size=page_size)


@sla_router.post("/policies", response_model=SlaPolicyResponse, status_code=201)
async def create_policy(
    body: SlaPolicyCreate,
    service: SlaService = Depends(_get_service),
    _: None = Depends(require_permission(ADMIN_CONFIG)),
) -> SlaPolicyResponse:
    return await service.create_policy(body)


@sla_router.get("/policies/{policy_id}", response_model=SlaPolicyResponse)
async def get_policy(
    policy_id: UUID,
    service: SlaService = Depends(_get_service),
    _: None = Depends(require_permission(ADMIN_CONFIG)),
) -> SlaPolicyResponse:
    return await service.get_policy(policy_id)


@sla_router.patch("/policies/{policy_id}", response_model=SlaPolicyResponse)
async def update_policy(
    policy_id: UUID,
    body: SlaPolicyPatch,
    service: SlaService = Depends(_get_service),
    _: None = Depends(require_permission(ADMIN_CONFIG)),
) -> SlaPolicyResponse:
    return await service.update_policy(policy_id, body)


@sla_router.post("/policies/{policy_id}/deactivate", response_model=SlaPolicyResponse)
async def deactivate_policy(
    policy_id: UUID,
    service: SlaService = Depends(_get_service),
    _: None = Depends(require_permission(ADMIN_CONFIG)),
) -> SlaPolicyResponse:
    return await service.deactivate_policy(policy_id)


# ── SLA do Chamado ─────────────────────────────────────────────────────────────

@tickets_sla_router.get("/{ticket_id}/sla", response_model=SlaTicketResponse)
async def get_ticket_sla(
    ticket_id: UUID,
    service: SlaService = Depends(_get_service),
    _: None = Depends(require_permission(TICKET_READ)),
) -> SlaTicketResponse:
    return await service.get_ticket_sla(ticket_id)
