"""
Business logic for Staff Lease Management (additive feature).

Staff/admin have global access (Decision: matches feature-lavanya's
require_staff semantics - property managers aren't scoped to one
property), so unlike a per-owner design this needs no ownership-chain
check - only that the caller passed require_staff (see routers layer) and
that the lease exists.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lease_agreement import LeaseAgreement
from app.schemas.lease import LeaseEditIn, LeaseOut, StaffLeaseListItemOut


def _get_lease_or_404(db: Session, lease_id: uuid.UUID) -> LeaseAgreement:
    lease = db.get(LeaseAgreement, lease_id)
    if lease is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "LEASE_NOT_FOUND", "message": "Lease not found."},
        )
    return lease


def get_all_leases(db: Session, status_filter: str | None = None) -> list[StaffLeaseListItemOut]:
    query = select(LeaseAgreement)
    if status_filter:
        query = query.where(LeaseAgreement.status == status_filter)

    # Newest-added lease first by default - the frontend table lets staff
    # re-sort by any column, but this is what they see before touching
    # anything, so a just-signed-up resident is immediately visible.
    rows = db.execute(query.order_by(LeaseAgreement.created_at.desc())).scalars().all()
    return [StaffLeaseListItemOut.from_model(lease) for lease in rows]


def update_lease(db: Session, lease_id: uuid.UUID, payload: LeaseEditIn) -> LeaseOut:
    lease = _get_lease_or_404(db, lease_id)

    if lease.status not in ("pending", "active"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "LEASE_NOT_EDITABLE",
                "message": "Only pending or active leases can be edited.",
            },
        )

    new_end_date = payload.end_date if payload.end_date is not None else lease.end_date
    if new_end_date <= lease.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": "VALIDATION_ERROR", "message": "End date must be after the start date."},
        )

    if payload.monthly_rate is not None:
        if payload.monthly_rate <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error_code": "VALIDATION_ERROR", "message": "Monthly rent must be greater than zero."},
            )
        lease.monthly_rate = payload.monthly_rate

    if payload.end_date is not None:
        lease.end_date = payload.end_date
    if payload.renewal_date is not None:
        lease.renewal_date = payload.renewal_date

    db.commit()
    db.refresh(lease)
    return LeaseOut.from_model(lease)


def activate_lease(db: Session, lease_id: uuid.UUID) -> LeaseOut:
    lease = _get_lease_or_404(db, lease_id)

    if lease.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "LEASE_NOT_PENDING", "message": "Only pending leases can be activated."},
        )

    lease.status = "active"
    db.commit()
    db.refresh(lease)
    return LeaseOut.from_model(lease)


def renew_lease(db: Session, lease_id: uuid.UUID, new_end_date: date) -> LeaseOut:
    lease = _get_lease_or_404(db, lease_id)

    if lease.status not in ("active", "expired"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "LEASE_NOT_RENEWABLE",
                "message": "Only active or expired leases can be renewed.",
            },
        )

    if new_end_date <= lease.end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": "The new end date must be after the current end date.",
            },
        )

    lease.end_date = new_end_date
    lease.status = "active"
    lease.renewal_requested_at = None
    db.commit()
    db.refresh(lease)
    return LeaseOut.from_model(lease)


def terminate_lease(db: Session, lease_id: uuid.UUID) -> LeaseOut:
    lease = _get_lease_or_404(db, lease_id)

    if lease.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "LEASE_NOT_ACTIVE", "message": "Only active leases can be terminated."},
        )

    lease.status = "terminated"
    db.commit()
    db.refresh(lease)
    return LeaseOut.from_model(lease)
