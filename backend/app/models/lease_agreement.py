import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

LEASE_STATUSES = ("pending", "active", "expired", "terminated")


class LeaseAgreement(Base):
    __tablename__ = "lease_agreements"
    __table_args__ = (
        CheckConstraint(f"status IN {LEASE_STATUSES}", name="ck_lease_agreements_status"),
        CheckConstraint("monthly_rate > 0", name="ck_lease_agreements_monthly_rate"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    guest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guests.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    monthly_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    renewal_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    unit: Mapped["Unit"] = relationship()  # noqa: F821
    guest: Mapped["Guest"] = relationship()  # noqa: F821
    invoices: Mapped[list["RecurringInvoice"]] = relationship(back_populates="lease")  # noqa: F821
