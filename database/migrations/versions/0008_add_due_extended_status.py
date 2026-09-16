"""add due_extended to recurring_invoices payment_status

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-15

Invoices workflow ported from teammate feature-annapoorna's branch: staff
extending an invoice's due date (PATCH /invoices/{id}/due-date) sets the
invoice to "due_extended" so residents see it changed before they pay -
this was missed in the initial port (only "payment_submitted" was added in
migration 0007); confirmed against the branch's actual
test_lease_invoice_api.py::test_staff_can_extend_due_date_and_period_end_moves_with_it.
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

OLD_STATUSES = ("pending", "payment_submitted", "paid", "overdue", "cancelled")
NEW_STATUSES = ("pending", "payment_submitted", "paid", "overdue", "due_extended", "cancelled")


def upgrade() -> None:
    op.drop_constraint("ck_recurring_invoices_payment_status", "recurring_invoices", type_="check")
    op.create_check_constraint(
        "ck_recurring_invoices_payment_status", "recurring_invoices", f"payment_status IN {NEW_STATUSES}"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE recurring_invoices SET payment_status = 'pending' WHERE payment_status = 'due_extended'"
    )
    op.drop_constraint("ck_recurring_invoices_payment_status", "recurring_invoices", type_="check")
    op.create_check_constraint(
        "ck_recurring_invoices_payment_status", "recurring_invoices", f"payment_status IN {OLD_STATUSES}"
    )
