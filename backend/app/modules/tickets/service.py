from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.modules.catalog.repository import (
    CategoryRepository,
    PendingReasonRepository,
    PriorityRepository,
    StatusRepository,
)
from app.modules.equipments.repository import EquipmentRepository
from app.modules.locations.repository import LocationRepository
from app.modules.notifications.service import NotificationService
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
from app.modules.timeline.service import TimelineService
from app.modules.users.repository import UserRepository

if TYPE_CHECKING:
    # Avoids circular import at runtime — closures.service imports tickets.repository
    from app.modules.closures.service import ClosureService

# INV-03: state machine transitions are invariant of code; catalog only controls labels (ADR-0003)
_VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "new": frozenset({"in_progress"}),
    "in_progress": frozenset({"pending", "resolved"}),
    "pending": frozenset({"in_progress"}),
    "resolved": frozenset({"in_progress", "closed"}),
    "closed": frozenset(),
}

# Roles that can see all tickets in the tenant
_ADMIN_ROLES = frozenset({"admin", "supervisor"})
# Role that sees only their team's tickets + assigned
_TECH_ROLE = "technician"


class TicketService:
    def __init__(
        self,
        ticket_repo: TicketRepository,
        observer_repo: TicketObserverRepository,
        comment_repo: TicketCommentRepository,
        solution_repo: SolutionRepository,
        status_repo: StatusRepository,
        priority_repo: PriorityRepository,
        category_repo: CategoryRepository,
        pending_reason_repo: PendingReasonRepository,
        equipment_repo: EquipmentRepository,
        location_repo: LocationRepository,
        user_repo: UserRepository,
        timeline_svc: TimelineService,
        notification_svc: NotificationService,
        sla_svc: SlaService | None = None,
        closure_svc: ClosureService | None = None,
    ) -> None:
        self._tickets = ticket_repo
        self._observers = observer_repo
        self._comments = comment_repo
        self._solutions = solution_repo
        self._statuses = status_repo
        self._priorities = priority_repo
        self._categories = category_repo
        self._pending_reasons = pending_reason_repo
        self._equipments = equipment_repo
        self._locations = location_repo
        self._users = user_repo
        self._timeline = timeline_svc
        self._notifications = notification_svc
        self._sla = sla_svc
        self._closure = closure_svc

    # ── Create ────────────────────────────────────────────────────────────────

    async def create(self, data: TicketCreate, requester_id: UUID) -> TicketResponse:
        await self._validate_create_type_constraints(data)

        priority = await self._priorities.get(data.priority_id)
        if priority is None or not priority.is_active:
            raise NotFoundError("Prioridade não encontrada ou inativa.")

        if data.category_id:
            category = await self._categories.get(data.category_id)
            if category is None or not category.is_active:
                raise NotFoundError("Categoria não encontrada ou inativa.")

        if data.team_id:
            from app.modules.teams.repository import TeamRepository
            team_repo = TeamRepository(self._tickets.session, self._tickets.tenant_id)
            team = await team_repo.get(data.team_id)
            if team is None or not team.is_active:
                raise NotFoundError("Equipe não encontrada ou inativa.")

        initial_status = await self._statuses.find_by_code("new")
        if initial_status is None:
            raise BusinessRuleError("Status inicial 'new' não configurado para este tenant.")

        ticket = await self._tickets.create(
            {
                "type": data.type,
                "title": data.title,
                "description": data.description,
                "priority_id": data.priority_id,
                "status_id": initial_status.id,
                "category_id": data.category_id,
                "equipment_id": data.equipment_id,
                "location_id": data.location_id,
                "team_id": data.team_id,
                "requester_id": requester_id,
            }
        )
        await self._timeline.record_event(
            event_type="ticket_created",
            ticket_id=ticket.id,
            actor_id=requester_id,
        )
        await self._notifications.notify(
            event_type="ticket_created",
            ticket_id=ticket.id,
            actor_id=requester_id,
        )
        if self._sla:
            await self._sla.initialize_tracker(
                ticket_id=ticket.id,
                ticket_type=ticket.type,
                priority_id=ticket.priority_id,
                team_id=ticket.team_id,
                created_at=ticket.created_at,
            )
        return TicketResponse.model_validate(ticket)

    # ── Get / List ─────────────────────────────────────────────────────────────

    async def get(
        self, ticket_id: UUID, current_user_id: UUID, role_codes: set[str]
    ) -> TicketResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")
        await self._check_read_access(ticket, current_user_id, role_codes)
        return TicketResponse.model_validate(ticket)

    async def list(
        self,
        *,
        current_user_id: UUID,
        role_codes: set[str],
        page: int,
        page_size: int,
        type: str | None = None,
        status_code: str | None = None,
        priority_id: UUID | None = None,
        team_id: UUID | None = None,
        assignee_id: UUID | None = None,
        requester_id: UUID | None = None,
        equipment_id: UUID | None = None,
        location_id: UUID | None = None,
        search: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> TicketListResponse:
        visibility, team_ids = await self._resolve_visibility(current_user_id, role_codes)
        offset = (page - 1) * page_size
        filter_kwargs = dict(
            visibility=visibility,
            current_user_id=current_user_id,
            user_team_ids=team_ids,
            type=type,
            status_code=status_code,
            priority_id=priority_id,
            team_id=team_id,
            assignee_id=assignee_id,
            requester_id=requester_id,
            equipment_id=equipment_id,
            location_id=location_id,
            search=search,
            created_from=created_from,
            created_to=created_to,
        )
        items = await self._tickets.list_filtered(**filter_kwargs, offset=offset, limit=page_size)
        total = await self._tickets.count_filtered(**filter_kwargs)
        return TicketListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[TicketResponse.model_validate(t) for t in items],
        )

    # ── Assign ─────────────────────────────────────────────────────────────────

    async def assign(
        self, ticket_id: UUID, assignee_id: UUID, current_user_id: UUID
    ) -> TicketResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")

        current_status = await self._statuses.get(ticket.status_id)
        if current_status is None or current_status.code != "new":
            raise BusinessRuleError("Apenas chamados com status 'Novo' podem ser assumidos.")

        in_progress_status = await self._statuses.find_by_code("in_progress")
        if in_progress_status is None:
            raise BusinessRuleError("Status 'in_progress' não configurado para este tenant.")

        now = datetime.now(UTC)
        await self._tickets.update(
            ticket_id,
            {
                "status_id": in_progress_status.id,
                "assignee_id": assignee_id,
                "assigned_at": now,
            },
        )
        await self._timeline.record_event(
            event_type="ticket_assigned",
            ticket_id=ticket_id,
            actor_id=current_user_id,
            payload={"assignee_id": str(assignee_id)},
        )
        await self._notifications.notify(
            event_type="ticket_assigned",
            ticket_id=ticket_id,
            actor_id=current_user_id,
        )
        if self._sla:
            await self._sla.on_ticket_assigned(ticket_id=ticket_id, assigned_at=now)
        updated = await self._tickets.get(ticket_id)
        return TicketResponse.model_validate(updated)

    # ── Transition ─────────────────────────────────────────────────────────────

    async def transition(
        self,
        ticket_id: UUID,
        data: TicketTransition,
        current_user_id: UUID,
    ) -> TicketResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")

        current_status = await self._statuses.get(ticket.status_id)
        if current_status is None:
            raise BusinessRuleError("Status atual do chamado não encontrado.")

        self._validate_transition(current_status.code, data.to_status)

        if data.to_status == "pending":
            if not data.pending_reason_id:
                raise BusinessRuleError("Motivo de pendência é obrigatório.")
            reason = await self._pending_reasons.get(data.pending_reason_id)
            if reason is None or not reason.is_active:
                raise NotFoundError("Motivo de pendência não encontrado ou inativo.")

        if data.to_status == "resolved":
            if not data.solution_description or not data.solution_description.strip():
                raise BusinessRuleError("Descrição da solução é obrigatória.")

        target_status = await self._statuses.find_by_code(data.to_status)
        if target_status is None:
            raise BusinessRuleError(f"Status '{data.to_status}' não configurado para este tenant.")

        now = datetime.now(UTC)
        changes: dict = {"status_id": target_status.id}

        if data.to_status == "resolved":
            changes["resolved_at"] = now
            await self._solutions.create(
                {
                    "ticket_id": ticket_id,
                    "description": data.solution_description,
                    "resolved_by": current_user_id,
                    "resolved_at": now,
                }
            )
            if self._closure:
                await self._closure.create_validation(
                    ticket_id=ticket_id,
                    requester_id=ticket.requester_id,
                )

        if data.to_status == "closed":
            changes["closed_at"] = now

        await self._tickets.update(ticket_id, changes)
        await self._timeline.record_event(
            event_type=f"ticket_transitioned_to_{data.to_status}",
            ticket_id=ticket_id,
            actor_id=current_user_id,
            payload={"from_status": current_status.code, "to_status": data.to_status},
        )
        await self._notifications.notify(
            event_type=f"ticket_transitioned_to_{data.to_status}",
            ticket_id=ticket_id,
            actor_id=current_user_id,
        )
        if self._sla:
            if data.to_status == "pending":
                await self._sla.on_ticket_pending(ticket_id=ticket_id, paused_at=now)
            elif data.to_status == "in_progress" and current_status.code == "pending":
                await self._sla.on_ticket_resumed(ticket_id=ticket_id, resumed_at=now)
            elif data.to_status == "resolved":
                await self._sla.on_ticket_resolved(ticket_id=ticket_id, resolved_at=now)
        updated = await self._tickets.get(ticket_id)
        return TicketResponse.model_validate(updated)

    # ── Observers ──────────────────────────────────────────────────────────────

    async def add_observer(
        self,
        ticket_id: UUID,
        data: TicketObserverAdd,
        current_user_id: UUID,
    ) -> TicketObserverResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")

        user = await self._users.get(data.user_id)
        if user is None or not user.is_active:
            raise NotFoundError("Usuário não encontrado ou inativo.")

        existing = await self._observers.find(ticket_id, data.user_id)
        if existing is not None:
            raise BusinessRuleError("Usuário já é observador deste chamado.")

        observer = await self._observers.create(
            {"ticket_id": ticket_id, "user_id": data.user_id}
        )
        await self._timeline.record_event(
            event_type="observer_added",
            ticket_id=ticket_id,
            actor_id=current_user_id,
            payload={"user_id": str(data.user_id)},
        )
        return TicketObserverResponse.model_validate(observer)

    async def remove_observer(
        self,
        ticket_id: UUID,
        observer_user_id: UUID,
        current_user_id: UUID,
    ) -> None:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")

        observer = await self._observers.find(ticket_id, observer_user_id)
        if observer is None:
            raise NotFoundError("Observador não encontrado neste chamado.")

        await self._observers.delete(observer.id)
        await self._timeline.record_event(
            event_type="observer_removed",
            ticket_id=ticket_id,
            actor_id=current_user_id,
            payload={"user_id": str(observer_user_id)},
        )

    # ── Comments ───────────────────────────────────────────────────────────────

    async def add_comment(
        self,
        ticket_id: UUID,
        data: TicketCommentCreate,
        author_id: UUID,
    ) -> TicketCommentResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")

        if not await self._is_participant(ticket, author_id):
            raise ForbiddenError("Apenas participantes podem comentar neste chamado.")

        comment = await self._comments.create(
            {
                "ticket_id": ticket_id,
                "author_id": author_id,
                "content": data.content,
            }
        )
        await self._timeline.record_event(
            event_type="comment_added",
            ticket_id=ticket_id,
            actor_id=author_id,
        )
        await self._notifications.notify(
            event_type="comment_added",
            ticket_id=ticket_id,
            actor_id=author_id,
        )
        return TicketCommentResponse.model_validate(comment)

    async def edit_comment(
        self,
        ticket_id: UUID,
        comment_id: UUID,
        data: TicketCommentUpdate,
        author_id: UUID,
    ) -> TicketCommentResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")

        comment = await self._comments.find_editable(comment_id, author_id)
        if comment is None:
            raise BusinessRuleError(
                "Comentário não encontrado, não pertence a você ou janela de edição expirou (15 min)."  # noqa: E501
            )
        if comment.ticket_id != ticket_id:
            raise NotFoundError("Comentário não pertence a este chamado.")

        await self._comments.update(comment_id, {"content": data.content})
        updated = await self._comments.get(comment_id)
        return TicketCommentResponse.model_validate(updated)

    async def list_comments(
        self,
        ticket_id: UUID,
        current_user_id: UUID,
        role_codes: set[str],
        *,
        page: int,
        page_size: int,
    ) -> TicketCommentListResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")
        await self._check_read_access(ticket, current_user_id, role_codes)

        offset = (page - 1) * page_size
        items = await self._comments.list_for_ticket(ticket_id, offset=offset, limit=page_size)
        total = await self._comments.count_for_ticket(ticket_id)
        return TicketCommentListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[TicketCommentResponse.model_validate(c) for c in items],
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _validate_create_type_constraints(self, data: TicketCreate) -> None:
        if data.type == "industrial":
            if not data.equipment_id:
                raise BusinessRuleError("Chamado industrial exige equipamento.")
            equipment = await self._equipments.get(data.equipment_id)
            if equipment is None:
                raise NotFoundError("Equipamento não encontrado.")
            if not equipment.is_active:
                raise BusinessRuleError("Equipamento informado está inativo.")
        else:  # predial
            if not data.location_id:
                raise BusinessRuleError("Chamado predial exige local.")
            location = await self._locations.get(data.location_id)
            if location is None:
                raise NotFoundError("Local não encontrado.")
            if not location.is_active:
                raise BusinessRuleError("Local informado está inativo.")

    @staticmethod
    def _validate_transition(from_code: str, to_code: str) -> None:
        """INV-03: raises if transition is not in the allowed set (ADR-0003)."""
        allowed = _VALID_TRANSITIONS.get(from_code, frozenset())
        if to_code not in allowed:
            raise BusinessRuleError(
                f"Transição de '{from_code}' para '{to_code}' não é permitida."
            )

    async def _is_participant(self, ticket, user_id: UUID) -> bool:
        if ticket.requester_id == user_id or ticket.assignee_id == user_id:
            return True
        observer = await self._observers.find(ticket.id, user_id)
        return observer is not None

    async def _check_read_access(self, ticket, current_user_id: UUID, role_codes: set[str]) -> None:
        """Raises 404 if user cannot read this ticket (INV-02)."""
        if role_codes & _ADMIN_ROLES:
            return
        if _TECH_ROLE in role_codes:
            if ticket.assignee_id == current_user_id:
                return
            team_ids = await self._tickets.get_team_ids_for_user(current_user_id)
            if ticket.team_id and ticket.team_id in team_ids:
                return
        # Requester: must be requester or observer
        if ticket.requester_id == current_user_id:
            return
        observer = await self._observers.find(ticket.id, current_user_id)
        if observer is not None:
            return
        # INV-02: cross-tenant or invisible resource → 404, never 403
        raise NotFoundError("Chamado não encontrado.")

    async def _resolve_visibility(
        self, current_user_id: UUID, role_codes: set[str]
    ) -> tuple[str, list[UUID]]:
        if role_codes & _ADMIN_ROLES:
            return "all", []
        if _TECH_ROLE in role_codes:
            team_ids = await self._tickets.get_team_ids_for_user(current_user_id)
            return "team", team_ids
        return "own", []
