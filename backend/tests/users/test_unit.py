from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.modules.users.schemas import RoleAssignRequest, UserCreate, UserUpdate
from app.modules.users.service import UserService


def _make_service(
    *,
    users=None,
    roles=None,
    user_roles=None,
    permissions=None,
) -> UserService:
    return UserService(
        user_repo=users or AsyncMock(),
        role_repo=roles or AsyncMock(),
        user_role_repo=user_roles or AsyncMock(),
        permission_repo=permissions or AsyncMock(),
    )


def _mock_user(*, is_active=True, user_id=None, tenant_id=None):
    u = MagicMock()
    u.id = user_id or uuid4()
    u.tenant_id = tenant_id or uuid4()
    u.name = "Test User"
    u.email = "test@example.com"
    u.is_active = is_active
    u.user_roles = []
    return u


def _mock_role(code="admin"):
    r = MagicMock()
    r.id = uuid4()
    r.code = code
    r.name = code.title()
    r.is_default = True
    return r


class TestCreateUser:
    async def test_duplicate_email_in_same_tenant_raises_conflict(self):
        users = AsyncMock()
        users.find_by_email.return_value = _mock_user()
        svc = _make_service(users=users)

        with pytest.raises(ConflictError):
            await svc.create_user(UserCreate(name="Dup", email="dup@t.com", password="12345678"))

    async def test_unique_email_creates_user(self):
        users = AsyncMock()
        users.find_by_email.return_value = None
        created = _mock_user()
        users.create.return_value = created
        svc = _make_service(users=users)

        payload = UserCreate(name="New", email="new@t.com", password="12345678")
        result = await svc.create_user(payload)
        assert result.id == created.id
        users.create.assert_called_once()


class TestUpdateUser:
    async def test_duplicate_email_on_update_raises_conflict(self):
        users = AsyncMock()
        existing = _mock_user()
        existing.email = "old@t.com"
        users.get.return_value = existing
        other = _mock_user()
        other.email = "new@t.com"
        users.find_by_email.return_value = other

        svc = _make_service(users=users)
        with pytest.raises(ConflictError):
            await svc.update_user(existing.id, UserUpdate(email="new@t.com"))

    async def test_same_email_unchanged_does_not_raise(self):
        users = AsyncMock()
        existing = _mock_user()
        existing.email = "same@t.com"
        users.get.return_value = existing
        refreshed = _mock_user()
        refreshed.id = existing.id
        refreshed.user_roles = []
        users.get_with_roles.return_value = refreshed

        svc = _make_service(users=users)
        await svc.update_user(existing.id, UserUpdate(email="same@t.com"))
        users.find_by_email.assert_not_called()


class TestRemoveRole:
    async def test_removing_admin_role_from_last_admin_raises(self):
        admin_role = _mock_role("admin")
        users = AsyncMock()
        users.get.return_value = _mock_user()
        users.count_active_admins.return_value = 0  # no other admins

        roles = AsyncMock()
        roles.get.return_value = admin_role

        user_roles = AsyncMock()

        svc = _make_service(users=users, roles=roles, user_roles=user_roles)
        with pytest.raises(BusinessRuleError):
            await svc.remove_role(uuid4(), admin_role.id)

    async def test_removing_admin_role_with_other_admins_succeeds(self):
        admin_role = _mock_role("admin")
        users = AsyncMock()
        users.get.return_value = _mock_user()
        users.count_active_admins.return_value = 1  # another admin exists

        roles = AsyncMock()
        roles.get.return_value = admin_role

        user_roles = AsyncMock()
        user_roles.remove.return_value = True

        svc = _make_service(users=users, roles=roles, user_roles=user_roles)
        await svc.remove_role(uuid4(), admin_role.id)
        user_roles.remove.assert_called_once()

    async def test_removing_non_admin_role_does_not_check_admin_count(self):
        tech_role = _mock_role("technician")
        users = AsyncMock()
        users.get.return_value = _mock_user()

        roles = AsyncMock()
        roles.get.return_value = tech_role

        user_roles = AsyncMock()
        user_roles.remove.return_value = True

        svc = _make_service(users=users, roles=roles, user_roles=user_roles)
        await svc.remove_role(uuid4(), tech_role.id)
        users.count_active_admins.assert_not_called()


class TestDeactivate:
    async def test_deactivating_last_admin_raises(self):
        admin_role = _mock_role("admin")
        ur = MagicMock()
        ur.role = admin_role

        users = AsyncMock()
        user = _mock_user()
        users.get.return_value = user
        users.count_active_admins.return_value = 0

        user_roles = AsyncMock()
        user_roles.list_for_user.return_value = [ur]

        svc = _make_service(users=users, user_roles=user_roles)
        with pytest.raises(BusinessRuleError):
            await svc.deactivate(user.id)

    async def test_deactivating_non_admin_succeeds(self):
        tech_ur = MagicMock()
        tech_ur.role = _mock_role("technician")

        users = AsyncMock()
        user = _mock_user()
        users.get.return_value = user
        users.count_active_admins.return_value = 0

        user_roles = AsyncMock()
        user_roles.list_for_user.return_value = [tech_ur]

        refreshed = _mock_user(is_active=False)
        refreshed.id = user.id
        refreshed.user_roles = [tech_ur]
        users.get_with_roles.return_value = refreshed

        svc = _make_service(users=users, user_roles=user_roles)
        result = await svc.deactivate(user.id)
        users.update.assert_called_once_with(user.id, {"is_active": False})
        assert result.is_active is False


class TestAssignRole:
    async def test_assigning_duplicate_role_raises_conflict(self):
        users = AsyncMock()
        users.get.return_value = _mock_user()

        role = _mock_role("technician")
        roles = AsyncMock()
        roles.get.return_value = role

        user_roles = AsyncMock()
        user_roles.find.return_value = MagicMock()  # already assigned

        svc = _make_service(users=users, roles=roles, user_roles=user_roles)
        with pytest.raises(ConflictError):
            await svc.assign_role(uuid4(), RoleAssignRequest(role_id=role.id))

    async def test_user_not_found_raises(self):
        users = AsyncMock()
        users.get.return_value = None
        svc = _make_service(users=users)

        with pytest.raises(NotFoundError):
            await svc.assign_role(uuid4(), RoleAssignRequest(role_id=uuid4()))
