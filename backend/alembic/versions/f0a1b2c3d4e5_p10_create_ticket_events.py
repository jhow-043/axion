"""p10_create_ticket_events

Revision ID: f0a1b2c3d4e5
Revises: e5f6a7b8c9d0
Create Date: 2026-06-03 14:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f0a1b2c3d4e5"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ticket_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ticket_events_tenant_id"), "ticket_events", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_ticket_events_ticket_id"), "ticket_events", ["ticket_id"], unique=False
    )
    op.create_index(
        op.f("ix_ticket_events_created_at"), "ticket_events", ["created_at"], unique=False
    )
    op.create_index(
        "ix_ticket_events_tenant_ticket", "ticket_events", ["tenant_id", "ticket_id"], unique=False
    )
    op.create_index(
        "ix_ticket_events_tenant_created", "ticket_events", ["tenant_id", "created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_ticket_events_tenant_created", table_name="ticket_events")
    op.drop_index("ix_ticket_events_tenant_ticket", table_name="ticket_events")
    op.drop_index(op.f("ix_ticket_events_created_at"), table_name="ticket_events")
    op.drop_index(op.f("ix_ticket_events_ticket_id"), table_name="ticket_events")
    op.drop_index(op.f("ix_ticket_events_tenant_id"), table_name="ticket_events")
    op.drop_table("ticket_events")
