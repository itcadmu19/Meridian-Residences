"""
AI-Generated Lease Agreement workflow - a resident's question about a
specific sent agreement version. `agreement_id` always points at the
version the resident was actually looking at when they asked, so a later
revision doesn't retroactively change what an old enquiry was about.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import GUID

STATUSES = ("open", "answered", "closed")


class LeaseEnquiry(Base):
    __tablename__ = "lease_enquiries"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    lease_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("lease_agreements.id"), nullable=False, index=True)
    agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreement_documents.id"), nullable=False, index=True)
    guest_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("guests.id"), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True, default="open")
    staff_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
