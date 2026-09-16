"""create shared baseline tables (guests, properties)

Revision ID: 0001
Revises:
Create Date: 2026-09-12

NOTE (Member 1 / lease story): guests/properties are cross-story shared
baseline entities (Project Design Document section 5.1), not owned by any
one story. Proposed here because nothing existed yet and the lease story
needs them first per the frozen integration sequence (section 26). If a
teammate has already created these independently, reconcile to one
migration rather than keeping both - see plan Decision 1.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("loyalty_tier", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("properties")
    op.drop_table("guests")
