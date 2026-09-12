"""
Team 5 entity (Project Design Document section 5.2). Owned by the lease
story (User Story 1).

`agreement_file_url` is an additive column beyond the frozen schema - see
the plan's Decision 7 for why it lives here (not the RAG documents table)
and why it's a simple nullable URL column rather than new infrastructure.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID


class LeaseAgreement(Base):
    __tablename__ = "lease_agreements"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    unit_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("units.id"), nullable=False, index=True
    )
    guest_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("guests.id"), nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    monthly_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    renewal_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)  # pending|active|expired|terminated
    agreement_file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    unit: Mapped["Unit"] = relationship(lazy="joined")
    guest: Mapped["Guest"] = relationship(lazy="joined")
