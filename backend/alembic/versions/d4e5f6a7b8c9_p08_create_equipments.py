"""p08_create_equipments

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-03 10:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "equipments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sector_id", sa.Uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("manufacturer", sa.String(length=255), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["sector_id"], ["sectors.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_equipments_tenant_code"),
    )
    op.create_index(op.f("ix_equipments_tenant_id"), "equipments", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_equipments_sector_id"), "equipments", ["sector_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_equipments_sector_id"), table_name="equipments")
    op.drop_index(op.f("ix_equipments_tenant_id"), table_name="equipments")
    op.drop_table("equipments")
