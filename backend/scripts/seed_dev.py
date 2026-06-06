"""Script de seed para desenvolvimento local.
Cria um tenant demo, usuário admin e popula catálogos padrão.

Uso: python scripts/seed_dev.py
"""

from __future__ import annotations

import asyncio
import os
import sys

# Garante que o diretório backend/ está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega .env antes de qualquer import de app
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

# Importa todos os models para criar as tabelas
import app.modules.auth.models  # noqa: F401
import app.modules.catalog.models  # noqa: F401
import app.modules.equipments.models  # noqa: F401
import app.modules.locations.models  # noqa: F401
import app.modules.teams.models  # noqa: F401
import app.modules.tickets.models  # noqa: F401
from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.modules.catalog.seed import seed_catalog_defaults  # noqa: E402
from app.modules.tenants.models import Tenant  # noqa: E402
from app.modules.users.models import Role, User, UserRole  # noqa: E402
from app.modules.users.seed import seed_default_roles_and_permissions  # noqa: E402

TENANT_NAME = "Demo Corp"
TENANT_SLUG = "demo"
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "Administrador"


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        async with session.begin():
            # Tenant
            from sqlalchemy import select

            existing = await session.execute(select(Tenant).where(Tenant.slug == TENANT_SLUG))
            tenant = existing.scalar_one_or_none()

            if tenant:
                print(f"Tenant '{TENANT_SLUG}' já existe — pulando criação.")
            else:
                tenant = Tenant(name=TENANT_NAME, slug=TENANT_SLUG)
                session.add(tenant)
                await session.flush()
                print(f"[OK] Tenant criado: {TENANT_NAME} (slug={TENANT_SLUG})")

            # Roles + permissions
            await seed_default_roles_and_permissions(session, tenant.id)
            await session.flush()
            print("[OK] Roles e permissões criadas.")

            # Catálogos padrão
            await seed_catalog_defaults(session, tenant.id)
            await session.flush()
            print("[OK] Catálogos padrão criados (prioridades, status).")

            # Admin user
            user_q = await session.execute(
                select(User).where(User.email == ADMIN_EMAIL, User.tenant_id == tenant.id)
            )
            user = user_q.scalar_one_or_none()

            if user:
                print(f"Usuário '{ADMIN_EMAIL}' já existe — pulando.")
            else:
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

    await engine.dispose()
    print("\nDONE! Seed concluído! Acesse: http://localhost:3001")
    print(f"   E-mail: {ADMIN_EMAIL}")
    print(f"   Senha:  {ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
