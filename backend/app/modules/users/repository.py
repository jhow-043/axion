from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import Permission, Role, RolePermission, User, UserRole
from app.shared.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    __model__ = User

    async def find_by_email(self, email: str) -> User | None:
        stmt = self._base_query().where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        *,
        name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        role_code: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[User]:
        stmt = self._base_query().options(selectinload(User.user_roles).selectinload(UserRole.role))
        if name:
            stmt = stmt.where(User.name.ilike(f"%{name}%"))
        if email:
            stmt = stmt.where(User.email.ilike(f"%{email}%"))
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if role_code:
            stmt = (
                stmt.join(UserRole, UserRole.user_id == User.id)
                .join(Role, Role.id == UserRole.role_id)
                .where(Role.code == role_code)
            )
        stmt = stmt.offset(offset).limit(limit).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def count_filtered(
        self,
        *,
        name: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        role_code: str | None = None,
    ) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(User).where(User.tenant_id == self.tenant_id)
        if name:
            stmt = stmt.where(User.name.ilike(f"%{name}%"))
        if email:
            stmt = stmt.where(User.email.ilike(f"%{email}%"))
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if role_code:
            stmt = (
                stmt.join(UserRole, UserRole.user_id == User.id)
                .join(Role, Role.id == UserRole.role_id)
                .where(Role.code == role_code)
            )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_with_roles(self, user_id: UUID) -> User | None:
        stmt = (
            self._base_query()
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_active_admins(self, exclude_user_id: UUID | None = None) -> int:
        """Counts active users with the admin role — used to guard the last-admin rule."""
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                User.tenant_id == self.tenant_id,
                User.is_active.is_(True),
                Role.code == "admin",
            )
        )
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()


class RoleRepository(BaseRepository[Role]):
    __model__ = Role

    async def find_by_code(self, code: str) -> Role | None:
        stmt = self._base_query().where(Role.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        stmt = self._base_query().order_by(Role.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class UserRoleRepository:
    """Manages user-role assignments. Tenant-scoped by querying with tenant_id directly."""

    def __init__(self, session: AsyncSession, tenant_id: UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def find(self, user_id: UUID, role_id: UUID) -> UserRole | None:
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.tenant_id == self.tenant_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def assign(self, user_id: UUID, role_id: UUID) -> UserRole:
        ur = UserRole(tenant_id=self.tenant_id, user_id=user_id, role_id=role_id)
        self.session.add(ur)
        await self.session.flush()
        return ur

    async def remove(self, user_id: UUID, role_id: UUID) -> bool:
        ur = await self.find(user_id, role_id)
        if ur is None:
            return False
        await self.session.delete(ur)
        await self.session.flush()
        return True

    async def list_for_user(self, user_id: UUID) -> list[UserRole]:
        stmt = (
            select(UserRole)
            .options(selectinload(UserRole.role))
            .where(UserRole.user_id == user_id, UserRole.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PermissionRepository:
    """Global (non-tenant) permission table queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.code)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_code(self, code: str) -> Permission | None:
        stmt = select(Permission).where(Permission.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_role(self, role_id: UUID) -> list[Permission]:
        stmt = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
