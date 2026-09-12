"""create units and lease_agreements tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-12

Team 5 entities owned by the lease story (Project Design Document sections
5.2/5.3). `agreement_file_url` on lease_agreements is an additive column
beyond the frozen schema - see plan Decision 7 (new nullable column for the
"Download agreement" feature, kept separate from the RAG documents table).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id"),
            nullable=False,
        ),
        sa.Column("unit_number", sa.String(length=50), nullable=False),
        sa.Column("unit_type", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("property_id", "unit_number", name="uq_units_property_unit_number"),
    )

    op.create_table(
        "lease_agreements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("units.id"), nullable=False
        ),
        sa.Column(
            "guest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("guests.id"), nullable=False
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("monthly_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("agreement_file_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_lease_agreements_unit_id", "lease_agreements", ["unit_id"])
    op.create_index("ix_lease_agreements_guest_id", "lease_agreements", ["guest_id"])
    op.create_index("ix_lease_agreements_status", "lease_agreements", ["status"])


def downgrade() -> None:
    op.drop_index("ix_lease_agreements_status", table_name="lease_agreements")
    op.drop_index("ix_lease_agreements_guest_id", table_name="lease_agreements")
    op.drop_index("ix_lease_agreements_unit_id", table_name="lease_agreements")
    op.drop_table("lease_agreements")
    op.drop_table("units")
