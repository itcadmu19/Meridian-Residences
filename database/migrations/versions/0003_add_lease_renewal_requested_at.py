"""add renewal_requested_at to lease_agreements

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-12

Additive column for the "Request renewal" feature - deliberately not a new
value on the frozen lease_status enum (pending/active/expired/terminated
stays as-is). See the plan's "Request Renewal" section for the endpoint
this backs.
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lease_agreements",
        sa.Column("renewal_requested_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lease_agreements", "renewal_requested_at")
