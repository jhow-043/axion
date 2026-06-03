from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base

# Import all models here so Alembic detects schema changes.
# Add new imports as each P## module is implemented:
from app.modules.auth.models import RefreshToken  # noqa: F401  # P03
from app.modules.catalog.models import (  # noqa: F401  # P07
    Category,
    PendingReason,
    Priority,
    Status,
)
from app.modules.equipments.models import Equipment  # noqa: F401  # P08
from app.modules.locations.models import Location, Sector  # noqa: F401  # P06
from app.modules.teams.models import Team, TeamMember  # noqa: F401  # P05
from app.modules.tenants.models import Tenant  # noqa: F401  # P01
from app.modules.users.models import (  # noqa: F401  # P03/P04
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
