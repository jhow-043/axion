from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select

from app.modules.timeline.models import TicketEvent
from app.shared.base_repository import BaseRepository


class TicketEventRepository(BaseRepository[TicketEvent]):
    __model__ = TicketEvent

    async def list_for_ticket(
        self, ticket_id: UUID, *, offset: int = 0, limit: int = 50
    ) -> list[TicketEvent]:
        stmt = (
            self._base_query()
            .where(TicketEvent.ticket_id == ticket_id)
            .order_by(TicketEvent.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_ticket(self, ticket_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(TicketEvent)
            .where(
                TicketEvent.tenant_id == self.tenant_id,
                TicketEvent.ticket_id == ticket_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
