from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select

from app.modules.attachments.models import Attachment
from app.shared.base_repository import BaseRepository


class AttachmentRepository(BaseRepository[Attachment]):
    __model__ = Attachment

    async def list_for_ticket(
        self, ticket_id: UUID, *, offset: int = 0, limit: int = 50
    ) -> list[Attachment]:
        stmt = (
            self._base_query()
            .where(Attachment.ticket_id == ticket_id)
            .order_by(Attachment.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_ticket(self, ticket_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Attachment)
            .where(
                Attachment.tenant_id == self.tenant_id,
                Attachment.ticket_id == ticket_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def find_by_storage_key(self, storage_key: str) -> Attachment | None:
        stmt = self._base_query().where(Attachment.storage_key == storage_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
