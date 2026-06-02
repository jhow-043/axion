from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.teams.schemas import MemberAddRequest, TeamCreate, TeamUpdate
from app.modules.teams.service import TeamService


def _make_service(
    *,
    team=None,
    find_by_name=None,
    user=None,
    existing_member=None,
) -> TeamService:
    team_repo = AsyncMock()
    team_repo.find_by_name.return_value = find_by_name
    team_repo.get.return_value = team
    team_repo.get_with_members.return_value = team
    team_repo.create.return_value = team
    team_repo.update.return_value = team

    member_repo = AsyncMock()
    member_repo.find.return_value = existing_member

    user_repo = AsyncMock()
    user_repo.get.return_value = user

    return TeamService(team_repo=team_repo, member_repo=member_repo, user_repo=user_repo)


def _make_team(*, is_active: bool = True, name: str = "Elétrica") -> MagicMock:
    team = MagicMock()
    team.id = uuid.uuid4()
    team.name = name
    team.description = None
    team.is_active = is_active
    team.tenant_id = uuid.uuid4()
    team.members = []
    return team


def _make_user(*, is_active: bool = True) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.is_active = is_active
    return user


class TestCreateTeam:
    async def test_duplicate_name_raises_conflict(self):
        existing = _make_team()
        service = _make_service(find_by_name=existing)
        with pytest.raises(ConflictError):
            await service.create_team(TeamCreate(name="Elétrica"))

    async def test_unique_name_creates_team(self):
        team = _make_team()
        service = _make_service(find_by_name=None, team=team)
        result = await service.create_team(TeamCreate(name="Elétrica"))
        assert result.name == "Elétrica"


class TestUpdateTeam:
    async def test_unknown_team_raises_not_found(self):
        service = _make_service(team=None)
        with pytest.raises(NotFoundError):
            await service.update_team(uuid.uuid4(), TeamUpdate(name="XX"))

    async def test_name_conflict_on_update_raises_conflict(self):
        current_team = _make_team(name="Elétrica")
        other_team = _make_team(name="Mecânica")
        service = _make_service(team=current_team, find_by_name=other_team)
        with pytest.raises(ConflictError):
            await service.update_team(current_team.id, TeamUpdate(name="Mecânica"))


class TestDeactivateTeam:
    async def test_unknown_team_raises_not_found(self):
        service = _make_service(team=None)
        with pytest.raises(NotFoundError):
            await service.deactivate_team(uuid.uuid4())

    async def test_already_inactive_raises_business_rule(self):
        team = _make_team(is_active=False)
        service = _make_service(team=team)
        with pytest.raises(BusinessRuleError):
            await service.deactivate_team(team.id)


class TestAddMember:
    async def test_unknown_team_raises_not_found(self):
        service = _make_service(team=None)
        with pytest.raises(NotFoundError):
            await service.add_member(uuid.uuid4(), MemberAddRequest(user_id=uuid.uuid4()))

    async def test_inactive_user_raises_business_rule(self):
        team = _make_team()
        user = _make_user(is_active=False)
        service = _make_service(team=team, user=user)
        with pytest.raises(BusinessRuleError):
            await service.add_member(team.id, MemberAddRequest(user_id=user.id))

    async def test_unknown_user_raises_not_found(self):
        team = _make_team()
        service = _make_service(team=team, user=None)
        with pytest.raises(NotFoundError):
            await service.add_member(team.id, MemberAddRequest(user_id=uuid.uuid4()))

    async def test_duplicate_member_raises_conflict(self):
        team = _make_team()
        user = _make_user()
        existing_member = MagicMock()
        service = _make_service(team=team, user=user, existing_member=existing_member)
        with pytest.raises(ConflictError):
            await service.add_member(team.id, MemberAddRequest(user_id=user.id))


class TestRemoveMember:
    async def test_unknown_team_raises_not_found(self):
        service = _make_service(team=None)
        with pytest.raises(NotFoundError):
            await service.remove_member(uuid.uuid4(), uuid.uuid4())

    async def test_nonexistent_member_raises_not_found(self):
        team = _make_team()
        service = _make_service(team=team)
        service._members.remove.return_value = False
        with pytest.raises(NotFoundError):
            await service.remove_member(team.id, uuid.uuid4())
