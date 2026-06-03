"""p11_create_attachments

Revision ID: a2b3c4d5e6f7
Revises: f0a1b2c3d4e5
Create Date: 2026-06-03 16:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: str | None = "f0a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("storage_key", sa.String(length=1000), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key", name="uq_attachments_storage_key"),
    )
    op.create_index(
        op.f("ix_attachments_tenant_id"), "attachments", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_attachments_ticket_id"), "attachments", ["ticket_id"], unique=False
    )
    op.create_index(
        "ix_attachments_tenant_ticket", "attachments", ["tenant_id", "ticket_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_attachments_tenant_ticket", table_name="attachments")
    op.drop_index(op.f("ix_attachments_ticket_id"), table_name="attachments")
    op.drop_index(op.f("ix_attachments_tenant_id"), table_name="attachments")
    op.drop_table("attachments")
