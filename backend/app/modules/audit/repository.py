from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select

from app.modules.audit.models import AuditLog
from app.shared.base_repository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    __model__ = AuditLog

    async def create_log(self, data: dict) -> AuditLog:
        # INV-01: tenant_id overridden by create()
        return await self.create(data)

    async def list_filtered(
        self,
        *,
        actor_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        action: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        stmt = self._base_query().order_by(AuditLog.created_at.desc())
        stmt = self._apply_filters(
            stmt,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            date_from=date_from,
            date_to=date_to,
        )
        result = await self.session.execute(stmt.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        actor_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        action: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        stmt = (
            select(func.count()).select_from(AuditLog).where(AuditLog.tenant_id == self.tenant_id)
        )
        stmt = self._apply_filters(
            stmt,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            date_from=date_from,
            date_to=date_to,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def _apply_filters(self, stmt, **filters):
        if filters.get("actor_id") is not None:
            stmt = stmt.where(AuditLog.actor_id == filters["actor_id"])
        if filters.get("entity_type") is not None:
            stmt = stmt.where(AuditLog.entity_type == filters["entity_type"])
        if filters.get("entity_id") is not None:
            stmt = stmt.where(AuditLog.entity_id == filters["entity_id"])
        if filters.get("action") is not None:
            stmt = stmt.where(AuditLog.action == filters["action"])
        if filters.get("date_from") is not None:
            stmt = stmt.where(AuditLog.created_at >= filters["date_from"])
        if filters.get("date_to") is not None:
            stmt = stmt.where(AuditLog.created_at <= filters["date_to"])
        return stmt
