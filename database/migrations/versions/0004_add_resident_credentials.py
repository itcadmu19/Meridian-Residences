"""add resident_credentials table

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-14

Ported from teammate feature-lavanya's branch (Story 3 auth) rather than
inventing a separate login mechanism - see resident_credential.py's
docstring. Backs the Staff Lease Management feature: a real email/password
login (POST /auth/login) that mints a JWT carrying `role`, and
`require_staff` in core/security.py checks that role. `role` values used:
resident (default) | staff | admin - staff/admin already bypass the
per-guest IDOR check in authorize_lease_access, so no per-property scoping
table is needed (Decision: global staff access, matching feature-lavanya's
own require_staff semantics).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resident_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "guest_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("guests.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units.id"), nullable=False
        ),
        sa.Column("email", sa.String(length=150), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="resident"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("resident_credentials")
