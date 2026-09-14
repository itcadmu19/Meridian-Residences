from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

IssueType = Literal["plumbing", "electrical", "hvac", "appliance", "general", "other"]
Priority = Literal["low", "medium", "high", "urgent"]
TicketStatus = Literal["open", "assigned", "in_progress", "resolved", "cancelled"]


class MaintenanceTicketCreate(BaseModel):
    # unit_id/guest_id are intentionally absent — derived from the authenticated session,
    # never trusted from the client (Design Contract §16).
    issue_type: IssueType
    description: str = Field(min_length=1, max_length=2000)
    # Optional base64 data URL (e.g. "data:image/jpeg;base64,..."), capped well under typical request-body limits.
    photo_data_url: str | None = Field(default=None, max_length=1_400_000)


class MaintenanceTicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: Priority | None = None
    vendor_queue: str | None = None
    escalated: bool | None = None


class MaintenanceTicketResponse(BaseModel):
    id: UUID
    unit_id: UUID
    guest_id: UUID
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

    model_config = {"from_attributes": True}


class TriageResultResponse(BaseModel):
    ticket_id: UUID
    issue_type: IssueType
    priority: Priority
    vendor_queue: str
    escalated: bool
    reason: str
