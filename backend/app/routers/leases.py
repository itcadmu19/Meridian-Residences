"""
HTTP layer for User Story 1 - View Lease Details.

Frozen endpoints (Project Design Document section 9.2 / 17). No renamed or
additional sibling endpoints. No business logic here - see
app/services/lease_service.py for that.
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_guest_id
from app.schemas.common import ListResponse, Meta, SuccessResponse
from app.schemas.lease import LeaseListItemOut, LeaseOut, LeaseSummaryOut
from app.services import lease_service

router = APIRouter(tags=["leases"])


@router.get("/leases/{lease_id}", response_model=SuccessResponse[LeaseOut])
def get_lease(
    lease_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    lease = lease_service.get_lease_detail(db, lease_id, current_user)
    return SuccessResponse(
        data=lease,
        message="Lease details fetched successfully",
        meta=Meta(request_id=request.state.request_id),
    )


@router.get("/guests/{guest_id}/leases", response_model=ListResponse[LeaseListItemOut])
def get_guest_leases(
    guest_id: uuid.UUID,
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    leases, total = lease_service.get_leases_for_guest(db, guest_id, current_user, page, page_size)
    return ListResponse(
        data=leases,
        meta=Meta(request_id=request.state.request_id, page=page, page_size=page_size, total=total),
    )


@router.get("/leases/{lease_id}/summary", response_model=SuccessResponse[LeaseSummaryOut])
def get_lease_summary(
    lease_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    summary = lease_service.get_dashboard_summary(db, lease_id, current_user)
    return SuccessResponse(
        data=summary,
        message="Dashboard data fetched successfully",
        meta=Meta(request_id=request.state.request_id),
    )
