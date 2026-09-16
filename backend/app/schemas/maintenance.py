"""
Maintenance schemas - ported field-for-field from teammate feature-lavanya's
branch for the App-wide Login + Maintenance feature.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lease import GuestOut, UnitOut

IssueType = Literal["plumbing", "electrical", "hvac", "appliance", "general", "other"]
Priority = Literal["low", "medium", "high", "urgent"]
TicketStatus = Literal["open", "assigned", "in_progress", "resolved", "cancelled"]


class MaintenanceTicketCreate(BaseModel):
    # unit_id/guest_id are intentionally absent - derived from the
    # authenticated session, never trusted from the client (contract §16).
    issue_type: IssueType
    description: str = Field(min_length=1, max_length=2000)
    # Optional base64 data URL (e.g. "data:image/jpeg;base64,..."), capped
    # well under typical request-body limits.
    photo_data_url: str | None = Field(default=None, max_length=1_400_000)


class MaintenanceTicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: Priority | None = None
    vendor_queue: str | None = None
    escalated: bool | None = None


class MaintenanceTicketResponse(BaseModel):
    """`guest`/`unit` are additive (Staff Maintenance workflow) - every
    endpoint returns them via `from_model` below so staff see who raised a
    ticket, not just a bare `guest_id`."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    unit_id: UUID
    guest_id: UUID
    guest: GuestOut
    unit: UnitOut
    issue_type: IssueType
    description: str
    priority: Priority
    status: TicketStatus
    vendor_queue: str | None
    escalated: bool
    photo_data_url: str | None = None
    triage_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None

    @classmethod
    def from_model(cls, ticket) -> "MaintenanceTicketResponse":
        return cls(
            id=ticket.id,
            unit_id=ticket.unit_id,
            guest_id=ticket.guest_id,
            guest=GuestOut.model_validate(ticket.guest),
            unit=UnitOut.model_validate(ticket.unit),
            issue_type=ticket.issue_type,
            description=ticket.description,
            priority=ticket.priority,
            status=ticket.status,
            vendor_queue=ticket.vendor_queue,
            escalated=ticket.escalated,
            photo_data_url=ticket.photo_data_url,
            triage_reason=ticket.triage_reason,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            resolved_at=ticket.resolved_at,
        )


class TriageResultResponse(BaseModel):
    ticket_id: UUID
    issue_type: IssueType
    priority: Priority
    vendor_queue: str
    escalated: bool
    reason: str
