"""add agreement_documents and lease_enquiries tables

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-16

AI-Generated Lease Agreement workflow. `agreement_documents` is the
generated/reviewed agreement text (versioned, distinct from the
`lease_agreements` contract record); `lease_enquiries` is a resident's
question about a specific sent version.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agreement_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lease_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lease_agreements.id"), nullable=False),
        sa.Column("guest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("guests.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_fields", sa.JSON(), nullable=True),
        sa.Column("generated_by_guest_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by_guest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("guests.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agreement_documents_lease_id", "agreement_documents", ["lease_id"])
    op.create_index("ix_agreement_documents_guest_id", "agreement_documents", ["guest_id"])
    op.create_index("ix_agreement_documents_status", "agreement_documents", ["status"])

    op.create_table(
        "lease_enquiries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lease_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lease_agreements.id"), nullable=False),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agreement_documents.id"), nullable=False),
        sa.Column("guest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("guests.id"), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("reference", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("staff_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_lease_enquiries_lease_id", "lease_enquiries", ["lease_id"])
    op.create_index("ix_lease_enquiries_agreement_id", "lease_enquiries", ["agreement_id"])
    op.create_index("ix_lease_enquiries_guest_id", "lease_enquiries", ["guest_id"])
    op.create_index("ix_lease_enquiries_status", "lease_enquiries", ["status"])


def downgrade() -> None:
    op.drop_index("ix_lease_enquiries_status", table_name="lease_enquiries")
    op.drop_index("ix_lease_enquiries_guest_id", table_name="lease_enquiries")
    op.drop_index("ix_lease_enquiries_agreement_id", table_name="lease_enquiries")
    op.drop_index("ix_lease_enquiries_lease_id", table_name="lease_enquiries")
    op.drop_table("lease_enquiries")

    op.drop_index("ix_agreement_documents_status", table_name="agreement_documents")
    op.drop_index("ix_agreement_documents_guest_id", table_name="agreement_documents")
    op.drop_index("ix_agreement_documents_lease_id", table_name="agreement_documents")
    op.drop_table("agreement_documents")
