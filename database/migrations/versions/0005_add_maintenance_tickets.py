"""add maintenance_tickets table

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-14

Ported from teammate feature-lavanya's branch (Design Contract section 5.5)
for the App-wide Login + Maintenance feature. Same columns/check-constraints/
indexes as her version.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

ISSUE_TYPES = ("plumbing", "electrical", "hvac", "appliance", "general", "other")
PRIORITIES = ("low", "medium", "high", "urgent")
STATUSES = ("open", "assigned", "in_progress", "resolved", "cancelled")


def upgrade() -> None:
    op.create_table(
        "maintenance_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units.id"), nullable=False),
        sa.Column("guest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("guests.id"), nullable=False),
        sa.Column("issue_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="open"),
        sa.Column("vendor_queue", sa.String(length=100), nullable=True),
        sa.Column("escalated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(f"issue_type IN {ISSUE_TYPES}", name="ck_maintenance_tickets_issue_type"),
        sa.CheckConstraint(f"priority IN {PRIORITIES}", name="ck_maintenance_tickets_priority"),
        sa.CheckConstraint(f"status IN {STATUSES}", name="ck_maintenance_tickets_status"),
    )
    op.create_index("ix_maintenance_tickets_unit_id", "maintenance_tickets", ["unit_id"])
    op.create_index("ix_maintenance_tickets_guest_id", "maintenance_tickets", ["guest_id"])
    op.create_index("ix_maintenance_tickets_status", "maintenance_tickets", ["status"])


def downgrade() -> None:
    op.drop_index("ix_maintenance_tickets_status", table_name="maintenance_tickets")
    op.drop_index("ix_maintenance_tickets_guest_id", table_name="maintenance_tickets")
    op.drop_index("ix_maintenance_tickets_unit_id", table_name="maintenance_tickets")
    op.drop_table("maintenance_tickets")
