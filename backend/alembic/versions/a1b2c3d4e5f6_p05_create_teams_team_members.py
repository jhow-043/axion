"""p05_create_teams_team_members

Revision ID: a1b2c3d4e5f6
Revises: 7981c59a275b
Create Date: 2026-06-02 10:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "7981c59a275b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_teams_tenant_name"),
    )
    op.create_index(op.f("ix_teams_tenant_id"), "teams", ["tenant_id"], unique=False)
    op.create_table(
        "team_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_members_team_user"),
    )
    op.create_index(op.f("ix_team_members_tenant_id"), "team_members", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_team_members_tenant_id"), table_name="team_members")
    op.drop_table("team_members")
    op.drop_index(op.f("ix_teams_tenant_id"), table_name="teams")
    op.drop_table("teams")
