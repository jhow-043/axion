"""p20_hub_modules

Revision ID: a0b1c2d3e4f5
Revises: f1a2b3c4d5e6
Create Date: 2026-06-15 10:00:00.000000

"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "a0b1c2d3e4f5"
down_revision: str | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "modules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_modules_code"),
    )

    op.create_table(
        "tenant_modules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("module_id", sa.Uuid(), nullable=False),
        sa.Column(
            "enabled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "module_id", name="uq_tenant_modules_tenant_module"),
    )
    op.create_index("ix_tenant_modules_tenant_id", "tenant_modules", ["tenant_id"])

    bind = op.get_bind()
    now = datetime.now(UTC)
    module_id = uuid.uuid4()

    # Seed the 'manutencao' module into the global catalogue
    bind.execute(
        sa.text(
            "INSERT INTO modules "
            "(id, code, name, description, icon, sort_order, is_active, created_at, updated_at) "
            "VALUES "
            "(:id, :code, :name, :description, :icon, "
            ":sort_order, :is_active, :created_at, :updated_at)"
        ),
        {
            "id": module_id,
            "code": "manutencao",
            "name": "Gestão de Manutenção",
            "description": "Abertura, acompanhamento e encerramento de chamados de manutenção.",
            "icon": "Wrench",
            "sort_order": 0,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        },
    )

    # Data script: enable 'manutencao' for all existing active tenants (retrocompatibility)
    result = bind.execute(
        sa.text("SELECT id FROM tenants WHERE is_active = true AND deleted_at IS NULL")
    )
    tenant_rows = result.fetchall()
    for row in tenant_rows:
        bind.execute(
            sa.text(
                "INSERT INTO tenant_modules (id, tenant_id, module_id, enabled_at) "
                "VALUES (:id, :tenant_id, :module_id, :enabled_at)"
            ),
            {
                "id": uuid.uuid4(),
                "tenant_id": row[0],
                "module_id": module_id,
                "enabled_at": now,
            },
        )


def downgrade() -> None:
    op.drop_index("ix_tenant_modules_tenant_id", table_name="tenant_modules")
    op.drop_table("tenant_modules")
    op.drop_table("modules")
