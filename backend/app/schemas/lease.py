"""
Pydantic schemas for the lease story's three frozen endpoints.

Field names are snake_case per contract section 4. The inner shape of
`/leases/{id}/summary` is not specified by the frozen contract itself (only
the outer envelope is) - this file is the de facto documentation of that
shape, matching what the local frontend's Dashboard.jsx already expects.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer

# Contract section 4: "Money: decimal in DB; JSON number: 12500.00" - Pydantic
# v2 serializes bare Decimal fields as JSON strings by default (to avoid
# float precision loss), which violates that rule. This forces a plain JSON
# number on the wire while keeping Decimal for validation/business logic.
MoneyAmount = Annotated[Decimal, PlainSerializer(lambda v: float(v), return_type=float, when_used="json")]


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    unit_number: str
    unit_type: str | None = None


class PropertyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    address: str | None = None


class LeaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    unit_id: uuid.UUID
    guest_id: uuid.UUID
    unit: UnitOut
    property: PropertyOut
    start_date: date
    end_date: date
    monthly_rate: MoneyAmount
    renewal_date: date | None = None
    status: str
    agreement_file_url: str | None = None

    @classmethod
    def from_model(cls, lease) -> "LeaseOut":
        return cls(
            id=lease.id,
            unit_id=lease.unit_id,
            guest_id=lease.guest_id,
            unit=UnitOut.model_validate(lease.unit),
            property=PropertyOut.model_validate(lease.unit.property),
            start_date=lease.start_date,
            end_date=lease.end_date,
            monthly_rate=lease.monthly_rate,
            renewal_date=lease.renewal_date,
            status=lease.status,
            agreement_file_url=lease.agreement_file_url,
        )


class LeaseListItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    unit_id: uuid.UUID
    status: str
    start_date: date
    end_date: date
    monthly_rate: MoneyAmount


class NextPaymentOut(BaseModel):
    amount: MoneyAmount
    due_date: date


class ActivityItemOut(BaseModel):
    id: str
    type: str
    title: str
    description: str
    date: datetime


class LeaseSummaryOut(BaseModel):
    lease_id: uuid.UUID
    unit: UnitOut
    next_payment: NextPaymentOut | None = None
    open_requests: int = 0
    open_request_status: str | None = None
    lease_status: str
    lease_end_date: date
    activities: list[ActivityItemOut] = []
