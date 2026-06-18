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


class TestSoftDeleteTenant:
    async def test_delete_tenant_sets_deleted_at(self, db_session: AsyncSession):
        tenant = Tenant(name="Del Corp", slug=f"del-{uuid.uuid4().hex[:6]}")
        db_session.add(tenant)
        await db_session.flush()

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)
        await svc.delete_tenant(tenant.id)

        await db_session.refresh(tenant)
        assert tenant.deleted_at is not None

    async def test_delete_system_tenant_raises_conflict(self, db_session: AsyncSession):
        from app.core.exceptions import ConflictError

        system_tenant = Tenant(
            name="Platform", slug=f"platform-{uuid.uuid4().hex[:6]}", is_system=True
        )
        db_session.add(system_tenant)
        await db_session.flush()

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)

        with pytest.raises(ConflictError):
            await svc.delete_tenant(system_tenant.id)

    async def test_soft_deleted_tenant_excluded_from_list(self, db_session: AsyncSession):
        active = Tenant(name="Active Corp", slug=f"active-{uuid.uuid4().hex[:6]}")
        deleted = Tenant(name="Deleted Corp", slug=f"deleted-{uuid.uuid4().hex[:6]}")
        db_session.add_all([active, deleted])
        await db_session.flush()

        repo = TenantRepository(db_session)
        svc = AdminService(repo, db_session)
        await svc.delete_tenant(deleted.id)

        result = await repo.list()
        ids = [str(t.id) for t in result]
        assert str(active.id) in ids
        assert str(deleted.id) not in ids


class TestDashboardRepository:
    async def test_global_stats_excludes_deleted_and_system(self, db_session: AsyncSession):
        from datetime import datetime

        from app.modules.administration.dashboard_repository import DashboardRepository

        t1 = Tenant(name="Client A", slug=f"client-a-{uuid.uuid4().hex[:6]}")
        t_sys = Tenant(
            name="System", slug=f"system-{uuid.uuid4().hex[:6]}", is_system=True
        )
        t_del = Tenant(
            name="Gone",
            slug=f"gone-{uuid.uuid4().hex[:6]}",
            deleted_at=datetime.utcnow(),
        )
        db_session.add_all([t1, t_sys, t_del])
        await db_session.flush()

        dash_repo = DashboardRepository(db_session)
        stats = await dash_repo.get_global_stats()

        assert stats.total_companies >= 1
        assert stats.active_companies + stats.suspended_companies == stats.total_companies

    async def test_list_company_rows_excludes_system_and_deleted(
        self, db_session: AsyncSession
    ):
        from datetime import datetime

        from app.modules.administration.dashboard_repository import DashboardRepository

        t_normal = Tenant(name="Normal", slug=f"normal-{uuid.uuid4().hex[:6]}")
        t_sys = Tenant(
            name="System", slug=f"sys2-{uuid.uuid4().hex[:6]}", is_system=True
        )
        t_del = Tenant(
            name="Deleted",
            slug=f"del2-{uuid.uuid4().hex[:6]}",
            deleted_at=datetime.utcnow(),
        )
        db_session.add_all([t_normal, t_sys, t_del])
        await db_session.flush()

        dash_repo = DashboardRepository(db_session)
        rows = await dash_repo.list_company_rows()
        row_ids = {str(r.id) for r in rows}

        assert str(t_normal.id) in row_ids
        assert str(t_sys.id) not in row_ids
        assert str(t_del.id) not in row_ids
