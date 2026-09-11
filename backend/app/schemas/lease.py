from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class LeaseResponse(BaseModel):
    id: UUID
    unit_id: UUID
    guest_id: UUID
    start_date: date
    end_date: date
    monthly_rate: Decimal
    renewal_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime
    unit_number: str | None = None
    unit_type: str | None = None
    property_name: str | None = None
    guest_name: str | None = None
    guest_email: str | None = None

    model_config = {"from_attributes": True}


class LeaseSummaryResponse(BaseModel):
    lease: LeaseResponse
    upcoming_invoice_count: int
    outstanding_amount: Decimal
    open_maintenance_count: int
