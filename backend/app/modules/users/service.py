from __future__ import annotations

from uuid import UUID

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.modules.users.repository import (
    PermissionRepository,
    RoleRepository,
    UserRepository,
    UserRoleRepository,
)
from app.modules.users.schemas import (
    PermissionResponse,
    RoleAssignRequest,
    RoleResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        user_role_repo: UserRoleRepository,
        permission_repo: PermissionRepository,
    ) -> None:
        self._users = user_repo
        self._roles = role_repo
        self._user_roles = user_role_repo
        self._permissions = permission_repo

    async def create_user(self, data: UserCreate) -> UserResponse:
        existing = await self._users.find_by_email(data.email)
        if existing is not None:
            raise ConflictError("Email já cadastrado neste tenant.")

        user = await self._users.create(
            {
                "name": data.name,
                "email": data.email,
                "password_hash": hash_password(data.password),
            }
        )
        return _to_response(user)

    async def get_user(self, user_id: UUID) -> UserResponse:
        user = await self._users.get_with_roles(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")
        return _to_response(user)

    async def list_users(
        self,
        *,
        page: int,
        page_size: int,
        name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        role_code: str | None = None,
    ) -> UserListResponse:
        offset = (page - 1) * page_size
        users = await self._users.list_filtered(
            name=name,
            email=email,
            is_active=is_active,
            role_code=role_code,
            offset=offset,
            limit=page_size,
        )
        total = await self._users.count_filtered(
            name=name, email=email, is_active=is_active, role_code=role_code
        )
        return UserListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[_to_response(u) for u in users],
        )

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        existing = await self._users.get(user_id)
        if existing is None:
            raise NotFoundError("Usuário não encontrado.")

        changes: dict = {}
        if data.name is not None:
            changes["name"] = data.name
        if data.email is not None and data.email != existing.email:
            conflict = await self._users.find_by_email(data.email)
            if conflict is not None:
                raise ConflictError("Email já cadastrado neste tenant.")
            changes["email"] = data.email

        if not changes:
            return await self.get_user(user_id)

        await self._users.update(user_id, changes)
        return await self.get_user(user_id)

    async def activate(self, user_id: UUID) -> UserResponse:
        user = await self._users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")
        await self._users.update(user_id, {"is_active": True})
        return await self.get_user(user_id)

    async def deactivate(self, user_id: UUID) -> UserResponse:
        user = await self._users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado.")
        # If this user is an admin, ensure there will still be at least one other active admin
        admin_count = await self._users.count_active_admins(exclude_user_id=user_id)
        if admin_count == 0:
            # Check if this user actually has the admin role before raising
            roles = await self._user_roles.list_for_user(user_id)
            if any(ur.role.code == "admin" for ur in roles):
                raise BusinessRuleError(
                    "Não é possível desativar o único administrador ativo do tenant."
                )
        await self._users.update(user_id, {"is_active": False})
        return await self.get_user(user_id)

    async def list_user_roles(self, user_id: UUID) -> list[RoleResponse]:
        if await self._users.get(user_id) is None:
            raise NotFoundError("Usuário não encontrado.")
        user_roles = await self._user_roles.list_for_user(user_id)
        return [RoleResponse.model_validate(ur.role) for ur in user_roles]

    async def assign_role(self, user_id: UUID, data: RoleAssignRequest) -> list[RoleResponse]:
        if await self._users.get(user_id) is None:
            raise NotFoundError("Usuário não encontrado.")
        role = await self._roles.get(data.role_id)
        if role is None:
            raise NotFoundError("Papel não encontrado.")
        existing = await self._user_roles.find(user_id, data.role_id)
        if existing is not None:
            raise ConflictError("Usuário já possui este papel.")
        await self._user_roles.assign(user_id, data.role_id)
        return await self.list_user_roles(user_id)

    async def remove_role(self, user_id: UUID, role_id: UUID) -> None:
        if await self._users.get(user_id) is None:
            raise NotFoundError("Usuário não encontrado.")
        role = await self._roles.get(role_id)
        if role is None:
            raise NotFoundError("Papel não encontrado.")

        # Guard: prevent removing the admin role if this is the last active admin (RN-03)
        if role.code == "admin":
            remaining_admins = await self._users.count_active_admins(exclude_user_id=user_id)
            if remaining_admins == 0:
                raise BusinessRuleError(
                    "Não é possível remover o papel de Admin do único administrador ativo."
                )

        removed = await self._user_roles.remove(user_id, role_id)
        if not removed:
            raise NotFoundError("Usuário não possui este papel.")

    async def list_roles(self) -> list[RoleResponse]:
        roles = await self._roles.list_all()
        return [RoleResponse.model_validate(r) for r in roles]

    async def list_permissions(self) -> list[PermissionResponse]:
        permissions = await self._permissions.list_all()
        return [PermissionResponse.model_validate(p) for p in permissions]


def _to_response(user) -> UserResponse:
    roles = []
    for ur in user.user_roles:
        roles.append(RoleResponse.model_validate(ur.role))
    return UserResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        roles=roles,
    )
