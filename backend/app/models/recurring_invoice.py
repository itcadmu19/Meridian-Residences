import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

PAYMENT_STATUSES = ("pending", "payment_submitted", "paid", "overdue", "cancelled")


class RecurringInvoice(Base):
    __tablename__ = "recurring_invoices"
    __table_args__ = (
        UniqueConstraint("lease_id", "billing_period_start", "billing_period_end", name="uq_recurring_invoices_lease_period"),
        CheckConstraint(f"payment_status IN {PAYMENT_STATUSES}", name="ck_recurring_invoices_payment_status"),
        CheckConstraint("amount > 0", name="ck_recurring_invoices_amount"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    lease_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("lease_agreements.id"), nullable=False)
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lease: Mapped["LeaseAgreement"] = relationship(back_populates="invoices")  # noqa: F821
