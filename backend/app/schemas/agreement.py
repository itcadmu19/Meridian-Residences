"""
AI-Generated Lease Agreement workflow schemas. Plain `str` status fields
throughout (no Literal/Enum), matching this codebase's existing convention
in schemas/lease.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GenerateAgreementIn(BaseModel):
    """Fields the lease/guest/unit/property tables don't already have.
    Everything except `security_deposit` has a sensible default applied
    server-side if omitted - see lease_agreement_agent.py."""

    security_deposit: Decimal = Field(..., gt=0)
    payment_due_day: int | None = Field(default=None, ge=1, le=28)
    notice_period_days: int | None = None
    maintenance_responsibility: str | None = None
    utilities_responsibility: str | None = None
    occupancy_terms: str | None = None
    late_payment_terms: str | None = None
    renewal_terms: str | None = None


class AgreementDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lease_id: uuid.UUID
    guest_id: uuid.UUID
    version: int
    status: str
    content: str
    structured_fields: dict | None = None
    generated_at: datetime
    sent_at: datetime | None = None
    accepted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AgreementUpdateIn(BaseModel):
    content: str = Field(..., min_length=1)


class EnquiryCreateIn(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    reference: str | None = Field(default=None, max_length=200)


class EnquiryRespondIn(BaseModel):
    response: str = Field(..., min_length=1)
    close: bool = False


class EnquiryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lease_id: uuid.UUID
    agreement_id: uuid.UUID
    guest_id: uuid.UUID
    subject: str
    message: str
    reference: str | None = None
    status: str
    staff_response: str | None = None
    created_at: datetime
    responded_at: datetime | None = None
    closed_at: datetime | None = None
