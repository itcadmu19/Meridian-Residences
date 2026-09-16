"""add photo_data_url and triage_reason to maintenance_tickets

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-15

Maintenance enhancements ported from a newer copy of teammate
feature-lavanya's branch: a resident can attach a photo when filing a
ticket, and the AI/rule-based triage reason is now persisted for the
ticket's detail view instead of being returned once and discarded.
"""

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("maintenance_tickets", sa.Column("photo_data_url", sa.Text(), nullable=True))
    op.add_column("maintenance_tickets", sa.Column("triage_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("maintenance_tickets", "triage_reason")
    op.drop_column("maintenance_tickets", "photo_data_url")
