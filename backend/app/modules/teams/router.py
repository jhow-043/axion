from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_any_permission, require_permission
from app.core.permissions import TEAM_MANAGE, TICKET_READ
from app.modules.teams.repository import TeamMemberRepository, TeamRepository
from app.modules.teams.schemas import (
    MemberAddRequest,
    MemberResponse,
    TeamCreate,
    TeamDetailResponse,
    TeamListResponse,
    TeamUpdate,
)
from app.modules.teams.service import TeamService
from app.modules.users.repository import UserRepository

router = APIRouter(prefix="/teams", tags=["teams"])


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TeamService:
    tenant_id = current_user.tenant_id
    return TeamService(
        team_repo=TeamRepository(db, tenant_id),
        member_repo=TeamMemberRepository(db, tenant_id),
        user_repo=UserRepository(db, tenant_id),
    )


@router.get("", response_model=TeamListResponse)
async def list_teams(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_active: bool | None = Query(default=None),
    service: TeamService = Depends(_get_service),
    _: object = Depends(require_any_permission(TEAM_MANAGE, TICKET_READ)),
) -> TeamListResponse:
    return await service.list_teams(page=page, page_size=page_size, is_active=is_active)


@router.post("", response_model=TeamDetailResponse, status_code=201)
async def create_team(
    body: TeamCreate,
    service: TeamService = Depends(_get_service),
    _: object = Depends(require_permission(TEAM_MANAGE)),
) -> TeamDetailResponse:
    return await service.create_team(body)


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: UUID,
    service: TeamService = Depends(_get_service),
    _: object = Depends(require_any_permission(TEAM_MANAGE, TICKET_READ)),
) -> TeamDetailResponse:
    return await service.get_team(team_id)


@router.patch("/{team_id}", response_model=TeamDetailResponse)
async def update_team(
    team_id: UUID,
    body: TeamUpdate,
    service: TeamService = Depends(_get_service),
    _: object = Depends(require_permission(TEAM_MANAGE)),
) -> TeamDetailResponse:
    return await service.update_team(team_id, body)


@router.post("/{team_id}/deactivate", response_model=TeamDetailResponse)
async def deactivate_team(
    team_id: UUID,
    service: TeamService = Depends(_get_service),
    _: object = Depends(require_permission(TEAM_MANAGE)),
) -> TeamDetailResponse:
    return await service.deactivate_team(team_id)


@router.get("/{team_id}/members", response_model=list[MemberResponse])
async def list_members(
    team_id: UUID,
    service: TeamService = Depends(_get_service),
    _: object = Depends(require_any_permission(TEAM_MANAGE, TICKET_READ)),
) -> list[MemberResponse]:
    return await service.list_members(team_id)


@router.post("/{team_id}/members", response_model=list[MemberResponse], status_code=200)
async def add_member(
    team_id: UUID,
    body: MemberAddRequest,
    service: TeamService = Depends(_get_service),
    _: object = Depends(require_permission(TEAM_MANAGE)),
) -> list[MemberResponse]:
    return await service.add_member(team_id, body)


@router.delete("/{team_id}/members/{user_id}", status_code=204)
async def remove_member(
    team_id: UUID,
    user_id: UUID,
    service: TeamService = Depends(_get_service),
    _: object = Depends(require_permission(TEAM_MANAGE)),
) -> None:
    await service.remove_member(team_id, user_id)
