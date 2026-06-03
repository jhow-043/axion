from __future__ import annotations

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.modules.tickets.repository import TicketObserverRepository, TicketRepository
from app.modules.timeline.repository import TicketEventRepository
from app.modules.timeline.schemas import ActorSummary, TicketEventResponse, TicketTimelineResponse
from app.modules.users.repository import UserRepository

# Mirror of tickets access rules — INV-02 applies here too (ADR-0002)
_ADMIN_ROLES = frozenset({"admin", "supervisor"})
_TECH_ROLE = "technician"


class TimelineService:
    def __init__(
        self,
        event_repo: TicketEventRepository,
        ticket_repo: TicketRepository,
        observer_repo: TicketObserverRepository,
        user_repo: UserRepository,
    ) -> None:
        self._events = event_repo
        self._tickets = ticket_repo
        self._observers = observer_repo
        self._users = user_repo

    async def record_event(
        self,
        *,
        event_type: str,
        ticket_id: UUID,
        actor_id: UUID | None,
        payload: dict | None = None,
    ) -> None:
        # Called synchronously within the caller's transaction — atomicity guaranteed
        await self._events.create(
            {
                "ticket_id": ticket_id,
                "actor_id": actor_id,
                "event_type": event_type,
                "payload": payload,
            }
        )

    async def list_events(
        self,
        ticket_id: UUID,
        current_user_id: UUID,
        role_codes: set[str],
        *,
        page: int,
        page_size: int,
    ) -> TicketTimelineResponse:
        ticket = await self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Chamado não encontrado.")
        await self._check_access(ticket, current_user_id, role_codes)

        offset = (page - 1) * page_size
        events = await self._events.list_for_ticket(ticket_id, offset=offset, limit=page_size)
        total = await self._events.count_for_ticket(ticket_id)

        actor_ids = {e.actor_id for e in events if e.actor_id is not None}
        actors: dict[UUID, ActorSummary] = {}
        for actor_id in actor_ids:
            user = await self._users.get(actor_id)
            if user:
                actors[actor_id] = ActorSummary(id=user.id, name=user.name)

        items = [
            TicketEventResponse(
                id=e.id,
                type=e.event_type,
                actor=actors.get(e.actor_id) if e.actor_id else None,
                payload=e.payload,
                created_at=e.created_at,
            )
            for e in events
        ]
        return TicketTimelineResponse(total=total, page=page, page_size=page_size, items=items)

    async def _check_access(self, ticket, current_user_id: UUID, role_codes: set[str]) -> None:
        """Same rules as ticket read access. INV-02: 404 not 403 (ADR-0002)."""
        if role_codes & _ADMIN_ROLES:
            return
        if _TECH_ROLE in role_codes:
            if ticket.assignee_id == current_user_id:
                return
            team_ids = await self._tickets.get_team_ids_for_user(current_user_id)
            if ticket.team_id and ticket.team_id in team_ids:
                return
        if ticket.requester_id == current_user_id:
            return
        observer = await self._observers.find(ticket.id, current_user_id)
        if observer is not None:
            return
        raise NotFoundError("Chamado não encontrado.")
