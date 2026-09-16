"""
Business logic for User Story 1 - View Lease Details.

Owns: LeaseAgreement, reads Unit/Guest/Property.
Cross-team data (invoices, maintenance) is read via other stories'
service-layer functions only (plan Decision 4) - never their tables
directly. Those services don't exist yet, so every cross-team call below
degrades gracefully (None/0) if the module or function isn't there yet.
Expected interfaces (to confirm with Members 2/3 - see plan Phase 6):

    invoice_service.get_latest_invoice_for_lease(lease_id: UUID)
        -> object with .id, .amount, .due_date, .generated_at, .paid_at
           (or None if the lease has no invoices)

    maintenance_service.get_open_ticket_stats(unit_id: UUID)
        -> object with .open_count, .status_summary, .recent_tickets
           (each recent ticket: .id, .issue_type, .status, .updated_at)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import CurrentUser, authorize_lease_access
from app.models.lease_agreement import LeaseAgreement
from app.schemas.lease import (
    ActivityItemOut,
    LeaseListItemOut,
    LeaseOut,
    LeaseSummaryOut,
    NextPaymentOut,
    RenewalRequestOut,
    UnitOut,
)
from app.services.lease_agreement_pdf import generate_lease_agreement_pdf

MAX_ACTIVITIES = 10


def _get_lease_or_none(db: Session, lease_id: uuid.UUID) -> LeaseAgreement | None:
    return db.get(LeaseAgreement, lease_id)


def get_lease_detail(db: Session, lease_id: uuid.UUID, current_user: CurrentUser) -> LeaseOut:
    lease = _get_lease_or_none(db, lease_id)
    authorize_lease_access(lease, current_user)  # raises 404 on missing/not-yours
    return LeaseOut.from_model(lease)


def get_leases_for_guest(
    db: Session,
    guest_id: uuid.UUID,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[LeaseListItemOut], int]:
    # A resident may only list their own leases (contract section 16.2).
    if current_user.role not in ("staff", "admin") and guest_id != current_user.guest_id:
        return [], 0

    base_query = select(LeaseAgreement).where(LeaseAgreement.guest_id == guest_id)
    total = len(db.execute(base_query).scalars().all())

    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    rows = (
        db.execute(
            base_query.order_by(LeaseAgreement.status, LeaseAgreement.start_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return [LeaseListItemOut.model_validate(lease) for lease in rows], total


def get_lease_agreement_pdf(db: Session, lease_id: uuid.UUID, current_user: CurrentUser) -> bytes:
    """Generates a real, personalized lease agreement PDF on demand from
    this lease's own data - see app/services/lease_agreement_pdf.py.
    `agreement_file_url` is kept only as an "is an agreement available"
    marker (e.g. a pending lease with nothing signed yet has none), not a
    real file path - nothing is read from disk here."""
    lease = _get_lease_or_none(db, lease_id)
    authorize_lease_access(lease, current_user)  # raises 404 on missing/not-yours

    if not lease.agreement_file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "AGREEMENT_NOT_FOUND", "message": "No agreement on file for this lease."},
        )

    return generate_lease_agreement_pdf(lease)


def request_lease_renewal(
    db: Session, lease_id: uuid.UUID, current_user: CurrentUser
) -> RenewalRequestOut:
    lease = _get_lease_or_none(db, lease_id)
    authorize_lease_access(lease, current_user)  # raises 404 on missing/not-yours

    if lease.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "LEASE_NOT_ACTIVE", "message": "Only active leases can request renewal."},
        )

    already_requested = lease.renewal_requested_at is not None
    if not already_requested:
        lease.renewal_requested_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(lease)

    return RenewalRequestOut(
        lease_id=lease.id,
        renewal_requested_at=lease.renewal_requested_at,
        already_requested=already_requested,
    )


def _next_payment_and_activity(lease_id: uuid.UUID) -> tuple[NextPaymentOut | None, list[ActivityItemOut]]:
    try:
        from app.services import invoice_service  # Member 2's story
    except ImportError:
        return None, []

    getter = getattr(invoice_service, "get_latest_invoice_for_lease", None)
    if getter is None:
        return None, []

    invoice = getter(lease_id)
    if invoice is None:
        return None, []

    next_payment = NextPaymentOut(amount=invoice.amount, due_date=invoice.due_date)

    activities: list[ActivityItemOut] = []
    generated_at = getattr(invoice, "generated_at", None)
    if generated_at:
        activities.append(
            ActivityItemOut(
                id=f"invoice-{invoice.id}",
                type="invoice",
                title="Invoice generated",
                description="A new invoice is ready to view.",
                date=generated_at,
            )
        )
    paid_at = getattr(invoice, "paid_at", None)
    if paid_at:
        activities.append(
            ActivityItemOut(
                id=f"payment-{invoice.id}",
                type="payment",
                title="Payment received",
                description="Your rent payment was recorded.",
                date=paid_at,
            )
        )
    return next_payment, activities


def _maintenance_summary_and_activity(
    unit_id: uuid.UUID,
) -> tuple[int, str | None, list[ActivityItemOut]]:
    try:
        from app.services import maintenance_service  # Member 3's story
    except ImportError:
        return 0, None, []

    getter = getattr(maintenance_service, "get_open_ticket_stats", None)
    if getter is None:
        return 0, None, []

    stats = getter(unit_id)
    if stats is None:
        return 0, None, []

    count = getattr(stats, "open_count", 0)
    status_summary = getattr(stats, "status_summary", None)

    activities: list[ActivityItemOut] = []
    for ticket in getattr(stats, "recent_tickets", None) or []:
        updated_at = getattr(ticket, "updated_at", None)
        if not updated_at:
            continue
        issue_type = getattr(ticket, "issue_type", "service")
        ticket_status = getattr(ticket, "status", "updated")
        activities.append(
            ActivityItemOut(
                id=f"maintenance-{ticket.id}",
                type="maintenance",
                title="Maintenance request updated",
                description=f"Your {issue_type} request is {ticket_status.replace('_', ' ')}.",
                date=updated_at,
            )
        )
    return count, status_summary, activities


def get_dashboard_summary(
    db: Session, lease_id: uuid.UUID, current_user: CurrentUser
) -> LeaseSummaryOut:
    lease = _get_lease_or_none(db, lease_id)
    authorize_lease_access(lease, current_user)  # raises 404 on missing/not-yours

    next_payment, invoice_activities = _next_payment_and_activity(lease.id)
    open_requests, open_request_status, maintenance_activities = _maintenance_summary_and_activity(
        lease.unit_id
    )

    lease_activities = [
        ActivityItemOut(
            id=f"lease-{lease.id}",
            type="lease",
            title="Lease agreement available",
            description="Your current lease is available to view.",
            date=lease.created_at,
        )
    ]

    activities = sorted(
        [*invoice_activities, *maintenance_activities, *lease_activities],
        key=lambda item: item.date,
        reverse=True,
    )[:MAX_ACTIVITIES]

    return LeaseSummaryOut(
        lease_id=lease.id,
        unit=UnitOut.model_validate(lease.unit),
        next_payment=next_payment,
        open_requests=open_requests,
        open_request_status=open_request_status,
        lease_status=lease.status,
        lease_end_date=lease.end_date,
        activities=activities,
    )
