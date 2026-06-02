from __future__ import annotations

from uuid import UUID

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.teams.repository import TeamMemberRepository, TeamRepository
from app.modules.teams.schemas import (
    MemberAddRequest,
    MemberResponse,
    TeamCreate,
    TeamDetailResponse,
    TeamListResponse,
    TeamResponse,
    TeamUpdate,
)
from app.modules.users.repository import UserRepository


class TeamService:
    def __init__(
        self,
        team_repo: TeamRepository,
        member_repo: TeamMemberRepository,
        user_repo: UserRepository,
    ) -> None:
        self._teams = team_repo
        self._members = member_repo
        self._users = user_repo

    async def create_team(self, data: TeamCreate) -> TeamDetailResponse:
        existing = await self._teams.find_by_name(data.name)
        if existing is not None:
            raise ConflictError("Nome de equipe já cadastrado neste tenant.")
        team = await self._teams.create({"name": data.name, "description": data.description})
        return await self.get_team(team.id)

    async def get_team(self, team_id: UUID) -> TeamDetailResponse:
        team = await self._teams.get_with_members(team_id)
        if team is None:
            raise NotFoundError("Equipe não encontrada.")
        return _to_detail_response(team)

    async def list_teams(
        self,
        *,
        page: int,
        page_size: int,
        is_active: bool | None = None,
    ) -> TeamListResponse:
        offset = (page - 1) * page_size
        teams = await self._teams.list_filtered(
            is_active=is_active,
            offset=offset,
            limit=page_size,
        )
        total = await self._teams.count_filtered(is_active=is_active)
        return TeamListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[_to_response(t) for t in teams],
        )

    async def update_team(self, team_id: UUID, data: TeamUpdate) -> TeamDetailResponse:
        team = await self._teams.get(team_id)
        if team is None:
            raise NotFoundError("Equipe não encontrada.")

        changes: dict = {}
        if data.name is not None and data.name != team.name:
            existing = await self._teams.find_by_name(data.name)
            if existing is not None:
                raise ConflictError("Nome de equipe já cadastrado neste tenant.")
            changes["name"] = data.name
        if data.description is not None:
            changes["description"] = data.description

        if changes:
            await self._teams.update(team_id, changes)
        return await self.get_team(team_id)

    async def deactivate_team(self, team_id: UUID) -> TeamDetailResponse:
        team = await self._teams.get_with_members(team_id)
        if team is None:
            raise NotFoundError("Equipe não encontrada.")
        if not team.is_active:
            raise BusinessRuleError("Equipe já está inativa.")
        await self._teams.update(team_id, {"is_active": False})
        return await self.get_team(team_id)

    async def list_members(self, team_id: UUID) -> list[MemberResponse]:
        team = await self._teams.get(team_id)
        if team is None:
            raise NotFoundError("Equipe não encontrada.")
        members = await self._members.list_for_team(team_id)
        return [MemberResponse(user_id=m.user_id, added_at=m.added_at) for m in members]

    async def add_member(self, team_id: UUID, data: MemberAddRequest) -> list[MemberResponse]:
        team = await self._teams.get(team_id)
        if team is None:
            raise NotFoundError("Equipe não encontrada.")

        # Validate user exists and is active in this tenant (RN-02)
        user = await self._users.get(data.user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")
        if not user.is_active:
            raise BusinessRuleError("Não é possível adicionar usuário inativo à equipe.")

        # Prevent duplicate members (RN-04)
        existing = await self._members.find(team_id, data.user_id)
        if existing is not None:
            raise ConflictError("Usuário já é membro desta equipe.")

        await self._members.add(team_id, data.user_id)
        return await self.list_members(team_id)

    async def remove_member(self, team_id: UUID, user_id: UUID) -> None:
        team = await self._teams.get(team_id)
        if team is None:
            raise NotFoundError("Equipe não encontrada.")
        removed = await self._members.remove(team_id, user_id)
        if not removed:
            raise NotFoundError("Usuário não é membro desta equipe.")


def _to_response(team) -> TeamResponse:
    return TeamResponse(
        id=team.id,
        tenant_id=team.tenant_id,
        name=team.name,
        description=team.description,
        is_active=team.is_active,
        member_count=len(team.members),
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


def _to_detail_response(team) -> TeamDetailResponse:
    return TeamDetailResponse(
        id=team.id,
        tenant_id=team.tenant_id,
        name=team.name,
        description=team.description,
        is_active=team.is_active,
        members=[MemberResponse(user_id=m.user_id, added_at=m.added_at) for m in team.members],
        created_at=team.created_at,
        updated_at=team.updated_at,
    )
