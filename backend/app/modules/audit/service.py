from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.modules.audit.repository import AuditLogRepository
from app.modules.audit.schemas import ActorSummary, AuditLogListResponse, AuditLogResponse
from app.modules.users.repository import UserRepository


class AuditService:
    def __init__(
        self,
        audit_repo: AuditLogRepository,
        user_repo: UserRepository,
    ) -> None:
        self._audit = audit_repo
        self._users = user_repo

    async def log(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: UUID,
        actor_id: UUID | None,
        before: dict | None = None,
        after: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Persist an immutable audit entry within the caller's transaction."""
        await self._audit.create_log(
            {
                "actor_id": actor_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "before": before,
                "after": after,
                "ip_address": ip_address,
            }
        )

    async def list_logs(
        self,
        *,
        actor_id: UUID | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        action: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> AuditLogListResponse:
        offset = (page - 1) * page_size
        logs = await self._audit.list_filtered(
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=page_size,
        )
        total = await self._audit.count_filtered(
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            date_from=date_from,
            date_to=date_to,
        )

        actor_ids = {log.actor_id for log in logs if log.actor_id is not None}
        actors: dict[UUID, ActorSummary] = {}
        for aid in actor_ids:
            user = await self._users.get(aid)
            if user:
                actors[aid] = ActorSummary(id=user.id, name=user.name)

        items = [
            AuditLogResponse(
                id=log.id,
                actor=actors.get(log.actor_id) if log.actor_id else None,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                before=log.before,
                after=log.after,
                ip_address=log.ip_address,
                created_at=log.created_at,
            )
            for log in logs
        ]
        return AuditLogListResponse(total=total, page=page, page_size=page_size, items=items)


def build_audit_service(db, tenant_id: UUID) -> AuditService:
    """Factory for use in router DI."""
    return AuditService(
        audit_repo=AuditLogRepository(db, tenant_id),
        user_repo=UserRepository(db, tenant_id),
    )
