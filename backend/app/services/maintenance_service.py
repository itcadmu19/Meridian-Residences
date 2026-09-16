"""
Maintenance ticket business logic - ported from teammate feature-lavanya's
branch (same authorization rules: resident sees/acts on own tickets only,
staff/admin see/act on all), adapted to this branch's `CurrentUser`/explicit
created_at-updated_at convention instead of her `core/deps.py` +
server-side timestamp defaults. Extended with the photo attachment,
persisted triage reason, real-AI triage, and staff-only `update_ticket`
ported from a newer copy of her branch (see maintenance_ticket.py's
docstring).

Note on `triage_ticket`'s access: that newer copy's own service function
required staff/admin, but its own frontend calls triage unconditionally
right after any resident creates a ticket, and its own test suite
(`test_triage_escalates_water_leak`) triages using a resident token and
asserts success. Two of three signals there agree triage should stay open
to the ticket's owner or staff - which is what this function already did
and still does; only `update_ticket` (unanimous across all three signals)
gained the staff-only restriction.

`get_open_ticket_stats` is additive - not part of either branch. It's the
interface `lease_service.py`'s dashboard summary already calls defensively
(see its `_maintenance_summary_and_activity` helper) and no-ops without;
adding it wires the Dashboard's "Open Requests" card to real data.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.maintenance_ai_agent import triage_with_ai
from app.ai.maintenance_triage_agent import TriageResult
from app.models.maintenance_ticket import MaintenanceTicket
from app.schemas.maintenance import MaintenanceTicketCreate, MaintenanceTicketUpdate

logger = logging.getLogger(__name__)

MAX_RECENT_TICKETS = 5


class TicketNotFoundError(Exception):
    pass


class TicketAccessDeniedError(Exception):
    pass


def create_ticket(
    db: Session, payload: MaintenanceTicketCreate, guest_id: uuid.UUID, unit_id: uuid.UUID
) -> MaintenanceTicket:
    now = datetime.now(timezone.utc)
    ticket = MaintenanceTicket(
        unit_id=unit_id,
        guest_id=guest_id,
        issue_type=payload.issue_type,
        description=payload.description,
        photo_data_url=payload.photo_data_url,
        priority="medium",
        status="open",
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    logger.info("Maintenance ticket %s created for guest_id=%s", ticket.id, guest_id)
    return ticket


def assert_can_access(ticket: MaintenanceTicket, guest_id: uuid.UUID, role: str) -> None:
    """A resident may only touch their own tickets; staff/admin may touch any."""
    if role in ("staff", "admin"):
        return
    if ticket.guest_id != guest_id:
        raise TicketAccessDeniedError("You do not have access to this maintenance ticket")


def list_tickets(
    db: Session,
    requesting_guest_id: uuid.UUID,
    role: str,
    guest_id: uuid.UUID | None = None,
    status: str | None = None,
    priority: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[MaintenanceTicket], int]:
    # Residents can never widen the query beyond their own tickets, even via
    # the guest_id filter - staff/admin may filter by any guest_id or see everyone's.
    if role not in ("staff", "admin"):
        guest_id = requesting_guest_id

    query = select(MaintenanceTicket)
    if guest_id is not None:
        query = query.where(MaintenanceTicket.guest_id == guest_id)
    if status is not None:
        query = query.where(MaintenanceTicket.status == status)
    if priority is not None:
        query = query.where(MaintenanceTicket.priority == priority)

    total = len(db.execute(query).scalars().all())

    page_size = min(max(page_size, 1), 100)
    page = max(page, 1)
    offset = (page - 1) * page_size

    items = (
        db.execute(query.order_by(MaintenanceTicket.created_at.desc()).offset(offset).limit(page_size))
        .scalars()
        .all()
    )
    return items, total


def get_ticket(db: Session, ticket_id: uuid.UUID, requesting_guest_id: uuid.UUID, role: str) -> MaintenanceTicket:
    ticket = db.get(MaintenanceTicket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(f"Maintenance ticket {ticket_id} not found")
    assert_can_access(ticket, requesting_guest_id, role)
    return ticket


def update_ticket(
    db: Session,
    ticket_id: uuid.UUID,
    payload: MaintenanceTicketUpdate,
    requesting_guest_id: uuid.UUID,
    role: str,
) -> MaintenanceTicket:
    if role not in ("staff", "admin"):
        raise TicketAccessDeniedError("Only staff can update maintenance tickets")

    ticket = get_ticket(db, ticket_id, requesting_guest_id, role)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(ticket, field, value)
    ticket.updated_at = datetime.now(timezone.utc)

    # Keep resolved_at consistent with status transitions rather than
    # trusting the client to set/clear it.
    if "status" in updates:
        ticket.resolved_at = ticket.updated_at if updates["status"] == "resolved" else None

    db.commit()
    db.refresh(ticket)
    logger.info("Maintenance ticket %s updated: %s", ticket.id, list(updates.keys()))
    return ticket


def delete_ticket(db: Session, ticket_id: uuid.UUID, requesting_guest_id: uuid.UUID, role: str) -> None:
    """A resident may delete only their own ticket; staff/admin cannot use
    this (no request from either signal to let them, unlike update/triage)."""
    ticket = get_ticket(db, ticket_id, requesting_guest_id, role)
    if ticket.guest_id != requesting_guest_id:
        raise TicketAccessDeniedError("Only the resident who submitted this request can delete it")

    db.delete(ticket)
    db.commit()
    logger.info("Maintenance ticket %s deleted by guest_id=%s", ticket_id, requesting_guest_id)


def triage_ticket(
    db: Session, ticket_id: uuid.UUID, requesting_guest_id: uuid.UUID, role: str
) -> tuple[MaintenanceTicket, TriageResult]:
    """Run the triage agent once, apply the result, and stop."""
    ticket = get_ticket(db, ticket_id, requesting_guest_id, role)

    result = triage_with_ai(ticket.description, fallback_issue_type=ticket.issue_type)

    ticket.issue_type = result.issue_type
    ticket.priority = result.priority
    ticket.vendor_queue = result.vendor_queue
    ticket.escalated = result.escalated
    ticket.triage_reason = result.reason
    if ticket.status == "open":
        ticket.status = "assigned"
    ticket.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(ticket)
    logger.info("Maintenance ticket %s triaged: priority=%s escalated=%s", ticket.id, ticket.priority, ticket.escalated)
    return ticket, result


@dataclass(frozen=True)
class RecentTicket:
    id: uuid.UUID
    issue_type: str
    status: str
    updated_at: datetime


@dataclass(frozen=True)
class OpenTicketStats:
    open_count: int
    status_summary: str | None
    recent_tickets: list[RecentTicket]


def get_open_ticket_stats(unit_id: uuid.UUID) -> OpenTicketStats | None:
    """Dashboard adapter (additive) - see module docstring."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        open_statuses = ("open", "assigned", "in_progress")
        query = select(MaintenanceTicket).where(
            MaintenanceTicket.unit_id == unit_id,
            MaintenanceTicket.status.in_(open_statuses),
        )
        tickets = db.execute(query.order_by(MaintenanceTicket.updated_at.desc())).scalars().all()

        if not tickets:
            return OpenTicketStats(open_count=0, status_summary=None, recent_tickets=[])

        in_progress_count = sum(1 for t in tickets if t.status == "in_progress")
        status_summary = f"{in_progress_count} in progress" if in_progress_count else None

        recent = [
            RecentTicket(id=t.id, issue_type=t.issue_type, status=t.status, updated_at=t.updated_at)
            for t in tickets[:MAX_RECENT_TICKETS]
        ]
        return OpenTicketStats(open_count=len(tickets), status_summary=status_summary, recent_tickets=recent)
    finally:
        db.close()
