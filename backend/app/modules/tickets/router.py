from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_role_codes, get_current_user, get_db, require_module, require_permission
from app.core.permissions import TICKET_ASSIGN, TICKET_CREATE, TICKET_READ, TICKET_TRANSITION
from app.modules.catalog.repository import (
    CategoryRepository,
    PendingReasonRepository,
    PriorityRepository,
    StatusRepository,
)
from app.modules.closures.repository import TenantSettingsRepository, ValidationRepository
from app.modules.closures.service import ClosureService
from app.modules.equipments.repository import EquipmentRepository
from app.modules.locations.repository import LocationRepository
from app.modules.notifications.service import build_notification_service
from app.modules.sla.repository import SlaPauseRepository, SlaPolicyRepository, SlaTrackerRepository
from app.modules.sla.service import SlaService
from app.modules.tickets.repository import (
    SolutionRepository,
    TicketCommentRepository,
    TicketObserverRepository,
    TicketRepository,
)
from app.modules.tickets.schemas import (
    TicketCommentCreate,
    TicketCommentListResponse,
    TicketCommentResponse,
    TicketCommentUpdate,
    TicketCreate,
    TicketListResponse,
    TicketObserverAdd,
    TicketObserverResponse,
    TicketResponse,
    TicketTransition,
)
from app.modules.tickets.service import TicketService
from app.modules.timeline.repository import TicketEventRepository
from app.modules.timeline.service import TimelineService
from app.modules.users.repository import UserRepository

router = APIRouter(prefix="/tickets", tags=["tickets"], dependencies=[Depends(require_module("manutencao"))])


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TicketService:
    tid = current_user.tenant_id
    return TicketService(
        ticket_repo=TicketRepository(db, tid),
        observer_repo=TicketObserverRepository(db, tid),
        comment_repo=TicketCommentRepository(db, tid),
        solution_repo=SolutionRepository(db, tid),
        status_repo=StatusRepository(db, tid),
        priority_repo=PriorityRepository(db, tid),
        category_repo=CategoryRepository(db, tid),
        pending_reason_repo=PendingReasonRepository(db, tid),
        equipment_repo=EquipmentRepository(db, tid),
        location_repo=LocationRepository(db, tid),
        user_repo=UserRepository(db, tid),
        timeline_svc=TimelineService(
            event_repo=TicketEventRepository(db, tid),
            ticket_repo=TicketRepository(db, tid),
            observer_repo=TicketObserverRepository(db, tid),
            user_repo=UserRepository(db, tid),
        ),
        notification_svc=build_notification_service(db, tid),
        sla_svc=SlaService(
            policy_repo=SlaPolicyRepository(db, tid),
            tracker_repo=SlaTrackerRepository(db, tid),
            pause_repo=SlaPauseRepository(db, tid),
            ticket_repo=TicketRepository(db, tid),
            notification_svc=build_notification_service(db, tid),
        ),
        closure_svc=ClosureService(
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
        ),
    )


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    body: TicketCreate,
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_CREATE)),
) -> TicketResponse:
    return await service.create(body, requester_id=current_user.id)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str | None = Query(default=None),
    status_code: str | None = Query(default=None),
    priority_id: UUID | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    team_id: UUID | None = Query(default=None),
    assignee_id: UUID | None = Query(default=None),
    requester_id: UUID | None = Query(default=None),
    equipment_id: UUID | None = Query(default=None),
    location_id: UUID | None = Query(default=None),
    sector_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
    role_codes: list[str] = Depends(get_current_role_codes),
) -> TicketListResponse:
    return await service.list(
        current_user_id=current_user.id,
        role_codes=set(role_codes),
        page=page,
        page_size=page_size,
        type=type,
        status_code=status_code,
        priority_id=priority_id,
        category_id=category_id,
        team_id=team_id,
        assignee_id=assignee_id,
        requester_id=requester_id,
        equipment_id=equipment_id,
        location_id=location_id,
        sector_id=sector_id,
        search=search,
        created_from=created_from,
        created_to=created_to,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
    role_codes: list[str] = Depends(get_current_role_codes),
) -> TicketResponse:
    return await service.get(ticket_id, current_user.id, set(role_codes))


@router.post("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: UUID,
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_ASSIGN)),
) -> TicketResponse:
    return await service.assign(
        ticket_id, assignee_id=current_user.id, current_user_id=current_user.id
    )


@router.post("/{ticket_id}/transition", response_model=TicketResponse)
async def transition_ticket(
    ticket_id: UUID,
    body: TicketTransition,
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_TRANSITION)),
) -> TicketResponse:
    return await service.transition(ticket_id, body, current_user_id=current_user.id)


@router.post("/{ticket_id}/observers", response_model=TicketObserverResponse, status_code=201)
async def add_observer(
    ticket_id: UUID,
    body: TicketObserverAdd,
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
) -> TicketObserverResponse:
    return await service.add_observer(ticket_id, body, current_user_id=current_user.id)


@router.delete("/{ticket_id}/observers/{observer_user_id}", status_code=204)
async def remove_observer(
    ticket_id: UUID,
    observer_user_id: UUID,
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_TRANSITION)),
) -> None:
    await service.remove_observer(ticket_id, observer_user_id, current_user_id=current_user.id)


@router.post("/{ticket_id}/comments", response_model=TicketCommentResponse, status_code=201)
async def add_comment(
    ticket_id: UUID,
    body: TicketCommentCreate,
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
) -> TicketCommentResponse:
    return await service.add_comment(ticket_id, body, author_id=current_user.id)


@router.patch("/{ticket_id}/comments/{comment_id}", response_model=TicketCommentResponse)
async def edit_comment(
    ticket_id: UUID,
    comment_id: UUID,
    body: TicketCommentUpdate,
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
) -> TicketCommentResponse:
    return await service.edit_comment(ticket_id, comment_id, body, author_id=current_user.id)


@router.get("/{ticket_id}/comments", response_model=TicketCommentListResponse)
async def list_comments(
    ticket_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: TicketService = Depends(_get_service),
    current_user=Depends(require_permission(TICKET_READ)),
    role_codes: list[str] = Depends(get_current_role_codes),
) -> TicketCommentListResponse:
    return await service.list_comments(
        ticket_id,
        current_user_id=current_user.id,
        role_codes=set(role_codes),
        page=page,
        page_size=page_size,
    )
