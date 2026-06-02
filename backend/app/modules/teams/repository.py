from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.teams.models import Team, TeamMember
from app.shared.base_repository import BaseRepository


class TeamRepository(BaseRepository[Team]):
    __model__ = Team

    async def find_by_name(self, name: str) -> Team | None:
        stmt = self._base_query().where(Team.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        *,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Team]:
        stmt = self._base_query().options(selectinload(Team.members))
        if is_active is not None:
            stmt = stmt.where(Team.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit).order_by(Team.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def count_filtered(self, *, is_active: bool | None = None) -> int:
        stmt = select(func.count()).select_from(Team).where(Team.tenant_id == self.tenant_id)
        if is_active is not None:
            stmt = stmt.where(Team.is_active == is_active)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_with_members(self, team_id: UUID) -> Team | None:
        stmt = self._base_query().options(selectinload(Team.members)).where(Team.id == team_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class TeamMemberRepository:
    """Manages team member assignments. Tenant-scoped."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def find(self, team_id: UUID, user_id: UUID) -> TeamMember | None:
        stmt = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
            TeamMember.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, team_id: UUID, user_id: UUID) -> TeamMember:
        member = TeamMember(
            tenant_id=self.tenant_id,
            team_id=team_id,
            user_id=user_id,
        )
        self.session.add(member)
        await self.session.flush()
        return member

    async def remove(self, team_id: UUID, user_id: UUID) -> bool:
        member = await self.find(team_id, user_id)
        if member is None:
            return False
        await self.session.delete(member)
        await self.session.flush()
        return True

    async def list_for_team(self, team_id: UUID) -> list[TeamMember]:
        stmt = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
