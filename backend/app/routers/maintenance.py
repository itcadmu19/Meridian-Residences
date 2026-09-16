"""
HTTP layer for Maintenance tickets - ported from teammate feature-lavanya's
branch, adapted to this branch's `core.security` instead of her `core.deps`.
No business logic here - see app/services/maintenance_service.py.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_guest_id
from app.schemas.common import Meta, SuccessResponse
from app.schemas.maintenance import (
    MaintenanceTicketCreate,
    MaintenanceTicketResponse,
    MaintenanceTicketUpdate,
    TriageResultResponse,
)
from app.services import maintenance_service
from app.services.maintenance_service import TicketAccessDeniedError, TicketNotFoundError

router = APIRouter(prefix="/maintenance-tickets", tags=["maintenance"])


def _not_found(ticket_id: UUID) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"message": f"Maintenance ticket {ticket_id} not found", "error_code": "TICKET_NOT_FOUND"},
    )


def _forbidden() -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"message": "You do not have access to this maintenance ticket", "error_code": "FORBIDDEN"},
    )


@router.post("", response_model=SuccessResponse[MaintenanceTicketResponse], status_code=201)
def create_ticket(
    payload: MaintenanceTicketCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    if current_user.unit_id is None:
        raise HTTPException(
            status_code=422,
            detail={"message": "No unit is associated with this account.", "error_code": "NO_UNIT"},
        )
    ticket = maintenance_service.create_ticket(db, payload, current_user.guest_id, current_user.unit_id)
    return SuccessResponse(data=MaintenanceTicketResponse.from_model(ticket))


@router.get("", response_model=SuccessResponse[list[MaintenanceTicketResponse]])
def list_tickets(
    guest_id: UUID | None = None,
    status: str | None = None,
    priority: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    items, total = maintenance_service.list_tickets(
        db, current_user.guest_id, current_user.role, guest_id, status, priority, page, page_size
    )
    data = [MaintenanceTicketResponse.from_model(item) for item in items]
    return SuccessResponse(data=data, meta=Meta(page=page, page_size=page_size, total=total))


@router.get("/{ticket_id}", response_model=SuccessResponse[MaintenanceTicketResponse])
def get_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    try:
        ticket = maintenance_service.get_ticket(db, ticket_id, current_user.guest_id, current_user.role)
    except TicketNotFoundError:
        raise _not_found(ticket_id)
    except TicketAccessDeniedError:
        raise _forbidden()
    return SuccessResponse(data=MaintenanceTicketResponse.from_model(ticket))


@router.patch("/{ticket_id}", response_model=SuccessResponse[MaintenanceTicketResponse])
def update_ticket(
    ticket_id: UUID,
    payload: MaintenanceTicketUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    try:
        ticket = maintenance_service.update_ticket(db, ticket_id, payload, current_user.guest_id, current_user.role)
    except TicketNotFoundError:
        raise _not_found(ticket_id)
    except TicketAccessDeniedError:
        raise _forbidden()
    return SuccessResponse(data=MaintenanceTicketResponse.from_model(ticket))


@router.delete("/{ticket_id}", status_code=204)
def delete_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    try:
        maintenance_service.delete_ticket(db, ticket_id, current_user.guest_id, current_user.role)
    except TicketNotFoundError:
        raise _not_found(ticket_id)
    except TicketAccessDeniedError:
        raise _forbidden()


@router.post("/{ticket_id}/triage", response_model=SuccessResponse[TriageResultResponse])
def triage_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    try:
        ticket, result = maintenance_service.triage_ticket(db, ticket_id, current_user.guest_id, current_user.role)
    except TicketNotFoundError:
        raise _not_found(ticket_id)
    except TicketAccessDeniedError:
        raise _forbidden()

    return SuccessResponse(
        data=TriageResultResponse(
            ticket_id=ticket.id,
            issue_type=result.issue_type,
            priority=result.priority,
            vendor_queue=result.vendor_queue,
            escalated=result.escalated,
            reason=result.reason,
        )
    )
