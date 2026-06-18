from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.administration.repository import TenantRepository
from app.modules.administration.schemas import TenantCreate
from app.modules.administration.service import AdminService
from app.modules.tenants.models import Tenant


class TestProvisionTenant:
    async def test_creates_tenant_record(self, db_session: AsyncSession):
        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)
        slug = f"new-corp-{uuid.uuid4().hex[:6]}"

        result = await svc.provision_tenant(
            TenantCreate(
                name="New Corp",
                slug=slug,
                admin_name="Admin",
                admin_email=f"admin-{uuid.uuid4().hex[:6]}@newcorp.com",
                admin_password="securepass123",
            )
        )

        assert result.name == "New Corp"
        assert result.slug == slug
        assert result.is_active is True

    async def test_duplicate_slug_raises_conflict(self, db_session: AsyncSession):
        from app.core.exceptions import ConflictError

        existing = Tenant(name="Existing", slug="existing-slug")
        db_session.add(existing)
        await db_session.flush()

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)

        with pytest.raises(ConflictError):
            await svc.provision_tenant(
                TenantCreate(
                    name="Dup",
                    slug="existing-slug",
                    admin_name="Admin",
                    admin_email="a@b.com",
                    admin_password="securepass123",
                )
            )

    async def test_provision_seeds_default_roles(self, db_session: AsyncSession):
        from sqlalchemy import select

        from app.modules.users.models import Role

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)
        result = await svc.provision_tenant(
            TenantCreate(
                name="Seeded Corp",
                slug=f"seeded-{uuid.uuid4().hex[:6]}",
                admin_name="Admin",
                admin_email=f"admin-{uuid.uuid4().hex[:6]}@seeded.com",
                admin_password="securepass123",
            )
        )

        roles_stmt = select(Role).where(Role.tenant_id == result.id)
        db_result = await db_session.execute(roles_stmt)
        role_codes = {r.code for r in db_result.scalars().all()}
        assert "admin" in role_codes
        assert "supervisor" in role_codes
        assert "technician" in role_codes
        assert "requester" in role_codes

    async def test_provision_creates_admin_user(self, db_session: AsyncSession):
        from sqlalchemy import select

        from app.modules.users.models import User

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)
        email = f"initadmin-{uuid.uuid4().hex[:6]}@corp.com"

        result = await svc.provision_tenant(
            TenantCreate(
                name="InitCorp",
                slug=f"init-{uuid.uuid4().hex[:6]}",
                admin_name="Init Admin",
                admin_email=email,
                admin_password="securepass123",
            )
        )

        user_stmt = select(User).where(User.tenant_id == result.id, User.email == email)
        db_result = await db_session.execute(user_stmt)
        user = db_result.scalar_one_or_none()
        assert user is not None
        assert user.is_active is True

    async def test_activate_deactivate_tenant(self, db_session: AsyncSession):
        tenant = Tenant(name="Toggle Corp", slug=f"toggle-{uuid.uuid4().hex[:6]}", is_active=True)
        db_session.add(tenant)
        await db_session.flush()

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)

        deactivated = await svc.deactivate_tenant(tenant.id)
        assert deactivated.is_active is False

        activated = await svc.activate_tenant(tenant.id)
        assert activated.is_active is True

    async def test_get_nonexistent_tenant_raises_not_found(self, db_session: AsyncSession):
        from app.core.exceptions import NotFoundError

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)

        with pytest.raises(NotFoundError):
            await svc.get_tenant(uuid.uuid4())
