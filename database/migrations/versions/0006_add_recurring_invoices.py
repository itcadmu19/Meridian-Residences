"""add recurring_invoices table

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-14

Ported from teammate feature-lavanya's branch for the App-wide Login +
Invoices feature. Same columns/check-constraints/unique-constraint as her
version.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

PAYMENT_STATUSES = ("pending", "paid", "overdue", "cancelled")


def upgrade() -> None:
    op.create_table(
        "recurring_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lease_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lease_agreements.id"), nullable=False
        ),
        sa.Column("billing_period_start", sa.Date(), nullable=False),
        sa.Column("billing_period_end", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("payment_status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "lease_id", "billing_period_start", "billing_period_end",
            name="uq_recurring_invoices_lease_period",
        ),
        sa.CheckConstraint(f"payment_status IN {PAYMENT_STATUSES}", name="ck_recurring_invoices_payment_status"),
        sa.CheckConstraint("amount > 0", name="ck_recurring_invoices_amount"),
    )
    op.create_index("ix_recurring_invoices_lease_id", "recurring_invoices", ["lease_id"])
    op.create_index("ix_recurring_invoices_payment_status", "recurring_invoices", ["payment_status"])


def downgrade() -> None:
    op.drop_index("ix_recurring_invoices_payment_status", table_name="recurring_invoices")
    op.drop_index("ix_recurring_invoices_lease_id", table_name="recurring_invoices")
    op.drop_table("recurring_invoices")
