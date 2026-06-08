from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select

from app.modules.teams.models import TeamMember
from app.modules.tickets.models import Solution, Ticket, TicketComment, TicketObserver
from app.shared.base_repository import BaseRepository


class TicketRepository(BaseRepository[Ticket]):
    __model__ = Ticket

    async def list_filtered(
        self,
        *,
        # visibility filter — computed by service from role_codes
        visibility: str = "all",  # "all" | "team" | "own"
        current_user_id: UUID | None = None,
        user_team_ids: list[UUID] | None = None,
        # query filters
        type: str | None = None,
        status_code: str | None = None,
        priority_id: UUID | None = None,
        category_id: UUID | None = None,
        team_id: UUID | None = None,
        assignee_id: UUID | None = None,
        requester_id: UUID | None = None,
        equipment_id: UUID | None = None,
        location_id: UUID | None = None,
        sector_id: UUID | None = None,
        search: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Ticket]:
        stmt = self._base_query()
        stmt = self._apply_visibility(stmt, visibility, current_user_id, user_team_ids or [])
        stmt = self._apply_filters(
            stmt,
            type,
            status_code,
            priority_id,
            category_id,
            team_id,
            assignee_id,
            requester_id,
            equipment_id,
            location_id,
            sector_id,
            search,
            created_from,
            created_to,
        )
        stmt = stmt.offset(offset).limit(limit).order_by(Ticket.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        visibility: str = "all",
        current_user_id: UUID | None = None,
        user_team_ids: list[UUID] | None = None,
        type: str | None = None,
        status_code: str | None = None,
        priority_id: UUID | None = None,
        category_id: UUID | None = None,
        team_id: UUID | None = None,
        assignee_id: UUID | None = None,
        requester_id: UUID | None = None,
        equipment_id: UUID | None = None,
        location_id: UUID | None = None,
        sector_id: UUID | None = None,
        search: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> int:
        stmt = self._base_query()
        stmt = self._apply_visibility(stmt, visibility, current_user_id, user_team_ids or [])
        stmt = self._apply_filters(
            stmt,
            type,
            status_code,
            priority_id,
            category_id,
            team_id,
            assignee_id,
            requester_id,
            equipment_id,
            location_id,
            sector_id,
            search,
            created_from,
            created_to,
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()

    def _apply_visibility(
        self, stmt, visibility: str, current_user_id: UUID | None, user_team_ids: list[UUID]
    ):
        if visibility == "own" and current_user_id:
            observer_subq = select(TicketObserver.ticket_id).where(
                TicketObserver.user_id == current_user_id,
                TicketObserver.tenant_id == self.tenant_id,
            )
            stmt = stmt.where(
                or_(
                    Ticket.requester_id == current_user_id,
                    Ticket.id.in_(observer_subq),
                )
            )
        elif visibility == "team" and current_user_id:
            conditions = [Ticket.assignee_id == current_user_id]
            if user_team_ids:
                conditions.append(Ticket.team_id.in_(user_team_ids))
            stmt = stmt.where(or_(*conditions))
        return stmt

    def _apply_filters(
        self,
        stmt,
        type,
        status_code,
        priority_id,
        category_id,
        team_id,
        assignee_id,
        requester_id,
        equipment_id,
        location_id,
        sector_id,
        search,
        created_from,
        created_to,
    ):
        if type:
            stmt = stmt.where(Ticket.type == type)
        if status_code:
            from app.modules.catalog.models import Status

            status_subq = (
                select(Status.id)
                .where(Status.code == status_code, Status.tenant_id == self.tenant_id)
                .scalar_subquery()
            )
            stmt = stmt.where(Ticket.status_id == status_subq)
        if priority_id:
            stmt = stmt.where(Ticket.priority_id == priority_id)
        if category_id:
            stmt = stmt.where(Ticket.category_id == category_id)
        if team_id:
            stmt = stmt.where(Ticket.team_id == team_id)
        if assignee_id:
            stmt = stmt.where(Ticket.assignee_id == assignee_id)
        if requester_id:
            stmt = stmt.where(Ticket.requester_id == requester_id)
        if equipment_id:
            stmt = stmt.where(Ticket.equipment_id == equipment_id)
        if location_id:
            stmt = stmt.where(Ticket.location_id == location_id)
        if sector_id:
            # Filter by equipment's sector — only industrial tickets have equipment
            from app.modules.equipments.models import Equipment

            sector_subq = (
                select(Equipment.id)
                .where(Equipment.sector_id == sector_id, Equipment.tenant_id == self.tenant_id)
                .scalar_subquery()
            )
            stmt = stmt.where(Ticket.equipment_id.in_(sector_subq))
        if search:
            stmt = stmt.where(Ticket.title.ilike(f"%{search}%"))
        if created_from:
            stmt = stmt.where(Ticket.created_at >= created_from)
        if created_to:
            stmt = stmt.where(Ticket.created_at <= created_to)
        return stmt

    async def get_team_ids_for_user(self, user_id: UUID) -> list[UUID]:
        """Returns IDs of teams the user belongs to in this tenant (for technician visibility)."""
        stmt = select(TeamMember.team_id).where(
            TeamMember.user_id == user_id,
            TeamMember.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class TicketObserverRepository(BaseRepository[TicketObserver]):
    __model__ = TicketObserver

    async def find(self, ticket_id: UUID, user_id: UUID) -> TicketObserver | None:
        stmt = self._base_query().where(
            TicketObserver.ticket_id == ticket_id,
            TicketObserver.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_ticket(self, ticket_id: UUID) -> list[TicketObserver]:
        stmt = self._base_query().where(TicketObserver.ticket_id == ticket_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class TicketCommentRepository(BaseRepository[TicketComment]):
    __model__ = TicketComment

    async def list_for_ticket(
        self,
        ticket_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[TicketComment]:
        stmt = (
            self._base_query()
            .where(TicketComment.ticket_id == ticket_id)
            .order_by(TicketComment.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_ticket(self, ticket_id: UUID) -> int:
        stmt = self._base_query().where(TicketComment.ticket_id == ticket_id)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        return result.scalar_one()

    async def find_editable(
        self, comment_id: UUID, author_id: UUID, edit_window_seconds: int = 900
    ) -> TicketComment | None:
        """Returns comment only if it belongs to author and is within edit window (15 min)."""
        comment = await self.get(comment_id)
        if comment is None or comment.author_id != author_id:
            return None
        age = (datetime.now(UTC) - comment.created_at.replace(tzinfo=UTC)).total_seconds()
        if age > edit_window_seconds:
            return None
        return comment


class SolutionRepository(BaseRepository[Solution]):
    __model__ = Solution

    async def find_by_ticket(self, ticket_id: UUID) -> Solution | None:
        stmt = self._base_query().where(Solution.ticket_id == ticket_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
