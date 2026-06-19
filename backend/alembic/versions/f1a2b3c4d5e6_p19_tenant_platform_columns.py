"""p19_tenant_platform_columns

Revision ID: f1a2b3c4d5e6
Revises: e6f7a8b9c0d1
Create Date: 2026-06-08 10:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # IF NOT EXISTS garante idempotência quando colunas já existem no schema
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP")
    # Cria índice somente se não existir
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tenants_deleted_at ON tenants (deleted_at)"
    )


def downgrade() -> None:
    op.drop_index("ix_tenants_deleted_at", table_name="tenants")
    op.drop_column("tenants", "deleted_at")
    op.drop_column("tenants", "is_system")
