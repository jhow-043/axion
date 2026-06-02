from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_permission
from app.core.permissions import USER_MANAGE, USER_READ
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
from app.modules.users.service import UserService

users_router = APIRouter(prefix="/users", tags=["users"])
roles_router = APIRouter(prefix="/roles", tags=["roles"])
permissions_router = APIRouter(prefix="/permissions", tags=["permissions"])


def _get_service(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserService:
    # tenant_id comes from current_user so get_current_user is guaranteed to have run first
    tenant_id = current_user.tenant_id
    return UserService(
        user_repo=UserRepository(db, tenant_id),
        role_repo=RoleRepository(db, tenant_id),
        user_role_repo=UserRoleRepository(db, tenant_id),
        permission_repo=PermissionRepository(db),
    )


# --- /users ---


@users_router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    name: str | None = Query(default=None),
    email: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    role_code: str | None = Query(default=None),
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_READ)),
) -> UserListResponse:
    return await service.list_users(
        page=page,
        page_size=page_size,
        name=name,
        email=email,
        is_active=is_active,
        role_code=role_code,
    )


@users_router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_MANAGE)),
) -> UserResponse:
    return await service.create_user(body)


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_READ)),
) -> UserResponse:
    return await service.get_user(user_id)


@users_router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_MANAGE)),
) -> UserResponse:
    return await service.update_user(user_id, body)


@users_router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_MANAGE)),
) -> UserResponse:
    return await service.activate(user_id)


@users_router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_MANAGE)),
) -> UserResponse:
    return await service.deactivate(user_id)


@users_router.get("/{user_id}/roles", response_model=list[RoleResponse])
async def list_user_roles(
    user_id: UUID,
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_READ)),
) -> list[RoleResponse]:
    return await service.list_user_roles(user_id)


@users_router.post("/{user_id}/roles", response_model=list[RoleResponse], status_code=200)
async def assign_role(
    user_id: UUID,
    body: RoleAssignRequest,
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_MANAGE)),
) -> list[RoleResponse]:
    return await service.assign_role(user_id, body)


@users_router.delete("/{user_id}/roles/{role_id}", status_code=204)
async def remove_role(
    user_id: UUID,
    role_id: UUID,
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_MANAGE)),
) -> None:
    await service.remove_role(user_id, role_id)


# --- /roles ---


@roles_router.get("", response_model=list[RoleResponse])
async def list_roles(
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_READ)),
) -> list[RoleResponse]:
    return await service.list_roles()


# --- /permissions ---


@permissions_router.get("", response_model=list[PermissionResponse])
async def list_permissions(
    service: UserService = Depends(_get_service),
    _: object = Depends(require_permission(USER_MANAGE)),
) -> list[PermissionResponse]:
    return await service.list_permissions()
