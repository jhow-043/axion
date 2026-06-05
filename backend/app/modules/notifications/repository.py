from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification, NotificationPreference
from app.shared.base_repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    __model__ = Notification

    async def list_for_recipient(
        self,
        recipient_id: UUID,
        *,
        is_read: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Notification]:
        stmt = self._base_query().where(Notification.recipient_id == recipient_id)
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_recipient(
        self,
        recipient_id: UUID,
        *,
        is_read: bool | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.tenant_id == self.tenant_id,
                Notification.recipient_id == recipient_id,
            )
        )
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def mark_all_read(self, recipient_id: UUID) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.tenant_id == self.tenant_id,
                Notification.recipient_id == recipient_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        result = await self.session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]


class NotificationPreferenceRepository(BaseRepository[NotificationPreference]):
    __model__ = NotificationPreference

    async def find(self, user_id: UUID, event_type: str) -> NotificationPreference | None:
        stmt = self._base_query().where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.event_type == event_type,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: UUID) -> list[NotificationPreference]:
        stmt = (
            self._base_query()
            .where(NotificationPreference.user_id == user_id)
            .order_by(NotificationPreference.event_type)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert(
        self,
        user_id: UUID,
        event_type: str,
        in_app_enabled: bool,
        email_enabled: bool,
    ) -> NotificationPreference:
        existing = await self.find(user_id, event_type)
        if existing is not None:
            updated = await self.update(
                existing.id,
                {"in_app_enabled": in_app_enabled, "email_enabled": email_enabled},
            )
            return updated  # type: ignore[return-value]
        return await self.create(
            {
                "user_id": user_id,
                "event_type": event_type,
                "in_app_enabled": in_app_enabled,
                "email_enabled": email_enabled,
            }
        )


class RecipientQueryRepository:
    """Tenant-scoped queries for notification recipient resolution."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def get_users_by_role_codes(self, role_codes: list[str]) -> list[UUID]:
        """Active users with any of the given role codes in this tenant."""
        from app.modules.users.models import Role, User, UserRole

        stmt = (
            select(User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                User.tenant_id == self.tenant_id,
                User.is_active.is_(True),
                Role.code.in_(role_codes),
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_team_users_by_role_codes(
        self, team_id: UUID, role_codes: list[str]
    ) -> list[UUID]:
        """Team members with any of the given role codes in this tenant."""
        from app.modules.teams.models import TeamMember
        from app.modules.users.models import Role, User, UserRole

        stmt = (
            select(TeamMember.user_id)
            .join(User, User.id == TeamMember.user_id)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                TeamMember.tenant_id == self.tenant_id,
                TeamMember.team_id == team_id,
                User.is_active.is_(True),
                Role.code.in_(role_codes),
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_observer_user_ids(self, ticket_id: UUID) -> list[UUID]:
        from app.modules.tickets.models import TicketObserver

        stmt = select(TicketObserver.user_id).where(
            TicketObserver.tenant_id == self.tenant_id,
            TicketObserver.ticket_id == ticket_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_email(self, user_id: UUID) -> str | None:
        from app.modules.users.models import User

        stmt = select(User.email).where(
            User.tenant_id == self.tenant_id,
            User.id == user_id,
            User.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
