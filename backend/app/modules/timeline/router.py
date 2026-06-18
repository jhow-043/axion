from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_role_codes, get_current_user, get_db, require_module, require_permission
from app.core.permissions import TICKET_READ
from app.modules.tickets.repository import TicketObserverRepository, TicketRepository
from app.modules.timeline.repository import TicketEventRepository
from app.modules.timeline.schemas import TicketTimelineResponse
from app.modules.timeline.service import TimelineService
from app.modules.users.repository import UserRepository

router = APIRouter(prefix="/tickets", tags=["timeline"], dependencies=[Depends(require_module("manutencao"))])


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TimelineService:
    tid = current_user.tenant_id
    return TimelineService(
        event_repo=TicketEventRepository(db, tid),
        ticket_repo=TicketRepository(db, tid),
        observer_repo=TicketObserverRepository(db, tid),
        user_repo=UserRepository(db, tid),
    )


@router.get("/{ticket_id}/timeline", response_model=TicketTimelineResponse)
async def get_ticket_timeline(
    ticket_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    service: TimelineService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
    role_codes: list[str] = Depends(get_current_role_codes),
) -> TicketTimelineResponse:
    return await service.list_events(
        ticket_id,
        current_user.id,
        set(role_codes),
        page=page,
        page_size=page_size,
    )
