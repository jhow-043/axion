"""Script de seed para desenvolvimento local.
Cria:
  1. Tenant-plataforma (is_system=True) com usuário SaaS Admin.
  2. Tenant demo com usuário admin.

Uso: python scripts/seed_dev.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

import app.modules.auth.models  # noqa: E402, F401
import app.modules.catalog.models  # noqa: E402, F401
import app.modules.equipments.models  # noqa: E402, F401
import app.modules.locations.models  # noqa: E402, F401
import app.modules.teams.models  # noqa: E402, F401
import app.modules.tickets.models  # noqa: E402, F401
from app.core.config import settings  # noqa: E402
from app.core.permissions import SYSTEM_ADMIN  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.modules.catalog.seed import seed_catalog_defaults  # noqa: E402
from app.modules.tenants.models import Tenant  # noqa: E402
from app.modules.users.models import Permission, Role, RolePermission, User, UserRole  # noqa: E402
from app.modules.users.seed import seed_default_roles_and_permissions  # noqa: E402

# ── Tenant da plataforma (is_system=True) ─────────────────────────────────────
PLATFORM_SLUG = "plataforma"
PLATFORM_NAME = "Plataforma"

SAAS_ADMIN_EMAIL = "admin@plataforma.local"
SAAS_ADMIN_PASSWORD = "admin123"
SAAS_ADMIN_NAME = "SaaS Admin"

# ── Tenant demo (empresa cliente de exemplo) ──────────────────────────────────
TENANT_NAME = "Demo Corp"
TENANT_SLUG = "demo"
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "Administrador"


async def _ensure_platform_tenant(session) -> Tenant:
    """Creates (or reuses) the reserved platform tenant with is_system=True."""
    q = await session.execute(select(Tenant).where(Tenant.slug == PLATFORM_SLUG))
    tenant = q.scalar_one_or_none()
    if tenant:
        print(f"Tenant-plataforma '{PLATFORM_SLUG}' já existe — pulando criação.")
        return tenant

    tenant = Tenant(name=PLATFORM_NAME, slug=PLATFORM_SLUG, is_system=True)
    session.add(tenant)
    await session.flush()
    print(f"[OK] Tenant-plataforma criado: {PLATFORM_NAME} (slug={PLATFORM_SLUG})")
    return tenant


async def _ensure_saas_admin(session, platform_tenant: Tenant) -> None:
    """Creates the initial SaaS Admin user in the platform tenant."""
    q = await session.execute(
        select(User).where(User.email == SAAS_ADMIN_EMAIL, User.tenant_id == platform_tenant.id)
    )
    if q.scalar_one_or_none():
        print(f"SaaS Admin '{SAAS_ADMIN_EMAIL}' já existe — pulando.")
        return

    # Ensure system_admin permission exists
    perm_q = await session.execute(select(Permission).where(Permission.code == SYSTEM_ADMIN))
    system_perm = perm_q.scalar_one_or_none()
    if system_perm is None:
        system_perm = Permission(code=SYSTEM_ADMIN, name="Super-administrador do sistema")
        session.add(system_perm)
        await session.flush()

    # Create (or reuse) the saas_admin role inside the platform tenant
    sa_role_q = await session.execute(
        select(Role).where(Role.tenant_id == platform_tenant.id, Role.code == "saas_admin")
    )
    sa_role = sa_role_q.scalar_one_or_none()
    if sa_role is None:
        sa_role = Role(
            tenant_id=platform_tenant.id,
            name="SaaS Admin",
            code="saas_admin",
            is_default=False,
        )
        session.add(sa_role)
        await session.flush()
        session.add(RolePermission(role_id=sa_role.id, permission_id=system_perm.id))
        await session.flush()

    user = User(
        tenant_id=platform_tenant.id,
        name=SAAS_ADMIN_NAME,
        email=SAAS_ADMIN_EMAIL,
        password_hash=hash_password(SAAS_ADMIN_PASSWORD),
        is_active=True,
    )
    session.add(user)
    await session.flush()
    session.add(UserRole(tenant_id=platform_tenant.id, user_id=user.id, role_id=sa_role.id))
    await session.flush()
    print(f"[OK] SaaS Admin criado: {SAAS_ADMIN_EMAIL} / {SAAS_ADMIN_PASSWORD}")


async def _ensure_demo_tenant(session) -> None:
    """Creates (or reuses) the demo tenant with a regular admin user."""
    q = await session.execute(select(Tenant).where(Tenant.slug == TENANT_SLUG))
    tenant = q.scalar_one_or_none()

    if tenant:
        print(f"Tenant '{TENANT_SLUG}' já existe — pulando criação.")
    else:
        tenant = Tenant(name=TENANT_NAME, slug=TENANT_SLUG)
        session.add(tenant)
        await session.flush()
        print(f"[OK] Tenant criado: {TENANT_NAME} (slug={TENANT_SLUG})")

    await seed_default_roles_and_permissions(session, tenant.id)
    await seed_catalog_defaults(session, tenant.id)
    await session.flush()

    user_q = await session.execute(
        select(User).where(User.email == ADMIN_EMAIL, User.tenant_id == tenant.id)
    )
    if user_q.scalar_one_or_none():
        print(f"Usuário '{ADMIN_EMAIL}' já existe — pulando.")
        return

    user = User(
        tenant_id=tenant.id,
        name=ADMIN_NAME,
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        is_active=True,
    )
    session.add(user)
    await session.flush()

    role_q = await session.execute(
        select(Role).where(Role.tenant_id == tenant.id, Role.code == "admin")
    )
    admin_role = role_q.scalar_one()
    session.add(UserRole(tenant_id=tenant.id, user_id=user.id, role_id=admin_role.id))
    await session.flush()
    print(f"[OK] Usuário admin criado: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        async with session.begin():
            platform_tenant = await _ensure_platform_tenant(session)
            await _ensure_saas_admin(session, platform_tenant)
            await _ensure_demo_tenant(session)

    await engine.dispose()
    print("\nDONE! Seed concluído! Acesse: http://localhost:3001")
    print(f"   SaaS Admin — E-mail: {SAAS_ADMIN_EMAIL}  |  Senha: {SAAS_ADMIN_PASSWORD}")
    print(f"   Admin demo — E-mail: {ADMIN_EMAIL}  |  Senha: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
