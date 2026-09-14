import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.maintenance_ai_agent import triage_with_ai
from app.core.config import settings
from app.models.maintenance_ticket import MaintenanceTicket
from app.schemas.maintenance import MaintenanceTicketCreate, MaintenanceTicketUpdate

logger = logging.getLogger(__name__)


class TicketNotFoundError(Exception):
    pass


class TicketAccessDeniedError(Exception):
    pass


def create_ticket(db: Session, payload: MaintenanceTicketCreate, guest_id: UUID, unit_id: UUID) -> MaintenanceTicket:
    ticket = MaintenanceTicket(
        unit_id=unit_id,
        guest_id=guest_id,
        issue_type=payload.issue_type,
        description=payload.description,
        photo_data_url=payload.photo_data_url,
        priority="medium",
        status="open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    logger.info("Maintenance ticket %s created for guest_id=%s", ticket.id, guest_id)
    return ticket


def assert_can_access(ticket: MaintenanceTicket, guest_id: UUID, role: str) -> None:
    """A resident may only touch their own tickets; staff/admin may touch any (Design Contract §16)."""
    if role in ("staff", "admin"):
        return
    if ticket.guest_id != guest_id:
        raise TicketAccessDeniedError("You do not have access to this maintenance ticket")


def list_tickets(
    db: Session,
    requesting_guest_id: UUID,
    role: str,
    guest_id: UUID | None = None,
    status: str | None = None,
    priority: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[MaintenanceTicket], int]:
    # Residents can never widen the query beyond their own tickets, even via the
    # guest_id filter — staff/admin may filter by any guest_id or see everyone's.
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


def get_ticket(db: Session, ticket_id: UUID, requesting_guest_id: UUID, role: str) -> MaintenanceTicket:
    ticket = db.get(MaintenanceTicket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(f"Maintenance ticket {ticket_id} not found")
    assert_can_access(ticket, requesting_guest_id, role)
    return ticket


def update_ticket(
    db: Session, ticket_id: UUID, payload: MaintenanceTicketUpdate, requesting_guest_id: UUID, role: str
) -> MaintenanceTicket:
    if role not in ("staff", "admin"):
        raise TicketAccessDeniedError("Only staff can update maintenance tickets")

    ticket = get_ticket(db, ticket_id, requesting_guest_id, role)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(ticket, field, value)

    # Keep resolved_at consistent with status transitions rather than trusting the client to set it.
    if "status" in updates:
        if updates["status"] == "resolved":
            ticket.resolved_at = datetime.now(timezone.utc)
        else:
            ticket.resolved_at = None

    db.commit()
    db.refresh(ticket)
    logger.info("Maintenance ticket %s updated: %s", ticket.id, list(updates.keys()))
    return ticket


def triage_ticket(
    db: Session, ticket_id: UUID, requesting_guest_id: UUID, role: str
) -> tuple[MaintenanceTicket, "TriageResult"]:
    """Run the triage agent once, apply the result, and stop (Design Contract §20)."""
    if role not in ("staff", "admin"):
        raise TicketAccessDeniedError("Only staff can triage maintenance tickets")

    ticket = get_ticket(db, ticket_id, requesting_guest_id, role)

    result = triage_with_ai(
        ticket.description,
        fallback_issue_type=ticket.issue_type,
        api_url=settings.ai_triage_api_url,
        api_key=settings.ai_triage_api_key,
        model=settings.ai_triage_model,
        timeout_seconds=settings.ai_triage_timeout_seconds,
    )

    ticket.issue_type = result.issue_type
    ticket.priority = result.priority
    ticket.vendor_queue = result.vendor_queue
    ticket.escalated = result.escalated
    ticket.triage_reason = result.reason
    if ticket.status == "open":
        ticket.status = "assigned"

    db.commit()
    db.refresh(ticket)
    logger.info("Maintenance ticket %s triaged: priority=%s escalated=%s", ticket.id, ticket.priority, ticket.escalated)
    return ticket, result
