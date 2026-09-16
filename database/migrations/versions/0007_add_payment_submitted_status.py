"""add payment_submitted to recurring_invoices payment_status

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-14

Invoices workflow ported from teammate feature-annapoorna's branch: a
resident's dummy payment submission stays "payment_submitted" until staff
approve it to "paid" (or flag it "overdue"), instead of residents
self-marking paid directly.
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

OLD_STATUSES = ("pending", "paid", "overdue", "cancelled")
NEW_STATUSES = ("pending", "payment_submitted", "paid", "overdue", "cancelled")


def upgrade() -> None:
    op.drop_constraint("ck_recurring_invoices_payment_status", "recurring_invoices", type_="check")
    op.create_check_constraint(
        "ck_recurring_invoices_payment_status", "recurring_invoices", f"payment_status IN {NEW_STATUSES}"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE recurring_invoices SET payment_status = 'pending' WHERE payment_status = 'payment_submitted'"
    )
    op.drop_constraint("ck_recurring_invoices_payment_status", "recurring_invoices", type_="check")
    op.create_check_constraint(
        "ck_recurring_invoices_payment_status", "recurring_invoices", f"payment_status IN {OLD_STATUSES}"
    )
