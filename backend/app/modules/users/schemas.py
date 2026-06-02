from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    is_default: bool


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    email: str
    is_active: bool
    roles: list[RoleResponse]


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserResponse]


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str


class RoleAssignRequest(BaseModel):
    role_id: UUID
