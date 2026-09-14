from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

PaymentStatus = Literal["pending", "payment_submitted", "paid", "overdue", "cancelled"]


class InvoiceResponse(BaseModel):
    id: UUID
    lease_id: UUID
    billing_period_start: date
    billing_period_end: date
    amount: Decimal
    due_date: date
    payment_status: PaymentStatus
    generated_at: datetime
    sent_at: datetime | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerateInvoiceRequest(BaseModel):
    lease_id: UUID
    billing_period_start: date
    billing_period_end: date
    due_date: date
    amount: Decimal | None = Field(default=None, gt=0)


class GenerateBatchRequest(BaseModel):
    billing_period_start: date
    billing_period_end: date
    due_date: date


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
    overdue_amount: Decimal
    insight: str


class OverdueSweepResult(BaseModel):
    flagged_count: int
