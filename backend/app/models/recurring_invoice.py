"""
Recurring invoice entity - ported from teammate feature-lavanya's branch for
the App-wide Login + Invoices feature. Same columns/constraints as her
version, adapted to this branch's GUID() type and explicit created_at/
updated_at convention (see maintenance_ticket.py's docstring for why).

`"payment_submitted"` and `"due_extended"` were added later (Invoices
workflow ported from teammate feature-annapoorna's branch) - see migrations
0007_add_payment_submitted_status.py and 0008_add_due_extended_status.py.
`"due_extended"` is set by `extend_due_date` (services/invoice_service.py)
so a resident sees their due date changed before they pay.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID

PAYMENT_STATUSES = ("pending", "payment_submitted", "paid", "overdue", "due_extended", "cancelled")


class RecurringInvoice(Base):
    __tablename__ = "recurring_invoices"
    __table_args__ = (
        UniqueConstraint(
            "lease_id", "billing_period_start", "billing_period_end",
            name="uq_recurring_invoices_lease_period",
        ),
        CheckConstraint(f"payment_status IN {PAYMENT_STATUSES}", name="ck_recurring_invoices_payment_status"),
        CheckConstraint("amount > 0", name="ck_recurring_invoices_amount"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    lease_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("lease_agreements.id"), nullable=False, index=True
    )
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    lease: Mapped["LeaseAgreement"] = relationship(lazy="joined")
