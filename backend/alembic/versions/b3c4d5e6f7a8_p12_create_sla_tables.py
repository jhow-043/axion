"""p12_create_sla_tables

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-06-03 18:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: str | None = "a2b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sla_policies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("ticket_type", sa.String(20), nullable=False),
        sa.Column("priority_id", sa.UUID(), nullable=False),
        sa.Column("team_id", sa.UUID(), nullable=True),
        sa.Column("attendance_minutes", sa.Integer(), nullable=False),
        sa.Column("resolution_minutes", sa.Integer(), nullable=False),
        sa.Column("alert_threshold_pct", sa.Integer(), nullable=False, server_default="80"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["priority_id"], ["priorities.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "ticket_type",
            "priority_id",
            "team_id",
            name="uq_sla_policies_tenant_type_priority_team",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index("ix_sla_policies_tenant_id", "sla_policies", ["tenant_id"])

    op.create_table(
        "sla_trackers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("policy_id", sa.UUID(), nullable=False),
        sa.Column("attendance_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attendance_status", sa.String(10), nullable=False, server_default="running"),
        sa.Column("attendance_met_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attendance_alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_status", sa.String(10), nullable=False, server_default="running"),
        sa.Column("resolution_met_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("total_paused_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["policy_id"], ["sla_policies.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id", name="uq_sla_trackers_ticket_id"),
    )
    op.create_index("ix_sla_trackers_tenant_id", "sla_trackers", ["tenant_id"])

    op.create_table(
        "sla_pauses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("tracker_id", sa.UUID(), nullable=False),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("minutes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tracker_id"], ["sla_trackers.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sla_pauses_tenant_id", "sla_pauses", ["tenant_id"])
    op.create_index("ix_sla_pauses_tracker_id", "sla_pauses", ["tracker_id"])


def downgrade() -> None:
    op.drop_table("sla_pauses")
    op.drop_table("sla_trackers")
    op.drop_table("sla_policies")
