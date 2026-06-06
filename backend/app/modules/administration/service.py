from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.modules.administration.repository import TenantRepository
from app.modules.administration.schemas import (
    TenantCreate,
    TenantListResponse,
    TenantResponse,
    TenantUpdate,
)
from app.modules.catalog.seed import seed_catalog_defaults
from app.modules.closures.models import TenantSettings
from app.modules.users.models import User
from app.modules.users.seed import seed_default_roles_and_permissions

if TYPE_CHECKING:
    from app.modules.audit.service import AuditService


class AdminService:
    def __init__(
        self,
        tenant_repo: TenantRepository,
        db: AsyncSession,
        audit_svc: AuditService | None = None,
        actor_id: UUID | None = None,
    ) -> None:
        self._tenants = tenant_repo
        self._db = db
        self._audit = audit_svc
        self._actor_id = actor_id

    async def list_tenants(self, *, page: int = 1, page_size: int = 20) -> TenantListResponse:
        offset = (page - 1) * page_size
        tenants = await self._tenants.list(offset=offset, limit=page_size)
        total = await self._tenants.count()
        return TenantListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=[TenantResponse.model_validate(t) for t in tenants],
        )

    async def get_tenant(self, tenant_id: UUID) -> TenantResponse:
        tenant = await self._tenants.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant não encontrado.")
        return TenantResponse.model_validate(tenant)

    async def provision_tenant(self, data: TenantCreate) -> TenantResponse:
        """Creates a tenant + seeds all default data + creates the initial admin user.
        All steps run in a single DB transaction via the caller's session."""
        if await self._tenants.get_by_slug(data.slug) is not None:
            raise ConflictError(f"Slug '{data.slug}' já está em uso.")

        tenant = await self._tenants.create({"name": data.name, "slug": data.slug})

        # Seed default roles, permissions, catalog (priorities/statuses), and settings
        await seed_default_roles_and_permissions(self._db, tenant.id)
        await seed_catalog_defaults(self._db, tenant.id)
        await _seed_tenant_settings(self._db, tenant.id)

        # Create initial admin user for the new tenant
        await _create_admin_user(self._db, tenant.id, data)

        if self._audit:
            await self._audit.log(
                action="tenant.provisioned",
                entity_type="Tenant",
                entity_id=tenant.id,
                actor_id=self._actor_id,
                after={"name": tenant.name, "slug": tenant.slug},
            )

        return TenantResponse.model_validate(tenant)

    async def update_tenant(self, tenant_id: UUID, data: TenantUpdate) -> TenantResponse:
        tenant = await self._tenants.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant não encontrado.")

        changes: dict = {}
        if data.name is not None:
            changes["name"] = data.name
        if data.slug is not None and data.slug != tenant.slug:
            if await self._tenants.get_by_slug(data.slug) is not None:
                raise ConflictError(f"Slug '{data.slug}' já está em uso.")
            changes["slug"] = data.slug
        if data.is_active is not None:
            changes["is_active"] = data.is_active

        if not changes:
            return TenantResponse.model_validate(tenant)

        before = {"name": tenant.name, "slug": tenant.slug, "is_active": tenant.is_active}
        updated = await self._tenants.update(tenant_id, changes)
        if self._audit:
            await self._audit.log(
                action="tenant.updated",
                entity_type="Tenant",
                entity_id=tenant_id,
                actor_id=self._actor_id,
                before=before,
                after=changes,
            )
        return TenantResponse.model_validate(updated)

    async def activate_tenant(self, tenant_id: UUID) -> TenantResponse:
        tenant = await self._tenants.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant não encontrado.")
        before = {"is_active": tenant.is_active}
        updated = await self._tenants.update(tenant_id, {"is_active": True})
        if self._audit:
            await self._audit.log(
                action="tenant.activated",
                entity_type="Tenant",
                entity_id=tenant_id,
                actor_id=self._actor_id,
                before=before,
                after={"is_active": True},
            )
        return TenantResponse.model_validate(updated)

    async def deactivate_tenant(self, tenant_id: UUID) -> TenantResponse:
        tenant = await self._tenants.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant não encontrado.")
        before = {"is_active": tenant.is_active}
        updated = await self._tenants.update(tenant_id, {"is_active": False})
        if self._audit:
            await self._audit.log(
                action="tenant.deactivated",
                entity_type="Tenant",
                entity_id=tenant_id,
                actor_id=self._actor_id,
                before=before,
                after={"is_active": False},
            )
        return TenantResponse.model_validate(updated)


async def _seed_tenant_settings(db: AsyncSession, tenant_id: UUID) -> None:
    """Creates TenantSettings with defaults if absent. Idempotent."""
    from sqlalchemy import select

    stmt = select(TenantSettings).where(TenantSettings.tenant_id == tenant_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        db.add(TenantSettings(tenant_id=tenant_id))
        await db.flush()


async def _create_admin_user(db: AsyncSession, tenant_id: UUID, data: TenantCreate) -> None:
    """Creates the initial admin user for a newly provisioned tenant."""
    from sqlalchemy import select

    from app.modules.users.models import Role, UserRole

    user = User(
        tenant_id=tenant_id,
        name=data.admin_name,
        email=data.admin_email,
        password_hash=hash_password(data.admin_password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    admin_role_stmt = select(Role).where(Role.tenant_id == tenant_id, Role.code == "admin")
    result = await db.execute(admin_role_stmt)
    admin_role = result.scalar_one_or_none()

    if admin_role is not None:
        db.add(UserRole(tenant_id=tenant_id, user_id=user.id, role_id=admin_role.id))
        await db.flush()
