"""
Invoice schemas - ported from teammate feature-lavanya's branch for the
App-wide Login + Invoices feature, extended with the approve-then-pay
workflow (InvoiceInsightResponse, DueDateUpdate, OverdueSweepResult, the
"payment_submitted"/"due_extended" statuses) ported from teammate
feature-annapoorna's branch. `amount`/`overdue_amount` use this app's
`MoneyAmount` (schemas/lease.py) instead of a bare Decimal, to keep "money
serializes as a JSON number" consistent with the rest of the app's contract.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lease import GuestOut, MoneyAmount, PropertyOut, UnitOut

PaymentStatus = Literal["pending", "payment_submitted", "paid", "overdue", "due_extended", "cancelled"]


class InvoiceResponse(BaseModel):
    """`guest`/`unit`/`property` are additive (Staff Invoices workflow) -
    every invoice endpoint returns them via `from_model` below so staff can
    always tell whose invoice they're looking at, not just a bare
    `lease_id`. A resident viewing their own invoices gets the same fields
    populated too (harmless, just unused by that view)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lease_id: UUID
    guest: GuestOut
    unit: UnitOut
    property: PropertyOut
    billing_period_start: date
    billing_period_end: date
    amount: MoneyAmount
    due_date: date
    payment_status: PaymentStatus
    generated_at: datetime
    sent_at: datetime | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, invoice) -> "InvoiceResponse":
        return cls(
            id=invoice.id,
            lease_id=invoice.lease_id,
            guest=GuestOut.model_validate(invoice.lease.guest),
            unit=UnitOut.model_validate(invoice.lease.unit),
            property=PropertyOut.model_validate(invoice.lease.unit.property),
            billing_period_start=invoice.billing_period_start,
            billing_period_end=invoice.billing_period_end,
            amount=invoice.amount,
            due_date=invoice.due_date,
            payment_status=invoice.payment_status,
            generated_at=invoice.generated_at,
            sent_at=invoice.sent_at,
            paid_at=invoice.paid_at,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
        )


class GenerateInvoiceRequest(BaseModel):
    """`billing_period_end`/`due_date` are no longer read - the service
    always derives them from `billing_period_start` (full calendar month,
    due the 10th of the following month; see
    invoice_service._billing_period_bounds). Kept optional here only so
    older callers that still send them don't fail validation."""

    lease_id: UUID
    billing_period_start: date
    billing_period_end: date | None = None
    due_date: date | None = None
    amount: Decimal | None = Field(default=None, gt=0)


class GenerateBatchRequest(BaseModel):
    """See GenerateInvoiceRequest's docstring - only billing_period_start
    is actually used."""

    billing_period_start: date
    billing_period_end: date | None = None
    due_date: date | None = None


class PaymentStatusUpdate(BaseModel):
    payment_status: PaymentStatus


class DueDateUpdate(BaseModel):
    due_date: date


class InvoiceBatchResult(BaseModel):
    generated_count: int
    duplicate_count: int
    failed_count: int
    invoice_ids: list[UUID]


class InvoiceInsightResponse(BaseModel):
    risk_level: Literal["low", "medium", "high"]
    late_payment_count: int
    total_invoices_considered: int
    average_days_late: float
    overdue_count: int
    overdue_amount: MoneyAmount
    insight: str


class OverdueSweepResult(BaseModel):
    flagged_count: int
