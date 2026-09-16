"""
AI-Generated Lease Agreement workflow - the generated agreement *document*
(the text a resident reads and accepts), distinct from `LeaseAgreement`
(`lease_agreements` table), which is the underlying lease contract record
(dates/rent/status). Named `AgreementDocument` specifically to avoid
colliding with that existing model.

Versioned: only the highest `version` for a given `lease_id` is "current".
Generating a new version while the previous one is still `sent_to_resident`
flips the old row to `superseded` first - it is never silently overwritten.
`guest_id` is denormalized from the parent lease (same convention as
`resident_credential.unit_id`) so ownership checks and resident-scoped
queries don't require a join back to `lease_agreements`.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import GUID

STATUSES = ("draft", "sent_to_resident", "accepted", "superseded")


class AgreementDocument(Base):
    __tablename__ = "agreement_documents"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    lease_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("lease_agreements.id"), nullable=False, index=True)
    guest_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("guests.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="draft")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    generated_by_guest_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_by_guest_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("guests.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
