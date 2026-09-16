"""
HTTP layer for Staff Lease Management (additive feature).

Does not touch the three frozen resident-facing GET endpoints in
leases.py - separate router, gated by require_staff (global access, no
per-property scoping - see staff_lease_service.py). No business logic
here - see app/services/staff_lease_service.py.
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, require_staff
from app.schemas.agreement import (
    AgreementDocumentOut,
    AgreementUpdateIn,
    EnquiryOut,
    EnquiryRespondIn,
    GenerateAgreementIn,
)
from app.schemas.common import ListResponse, Meta, SuccessResponse
from app.schemas.lease import LeaseEditIn, LeaseOut, LeaseRenewIn, StaffLeaseListItemOut
from app.services import agreement_service, staff_lease_service

router = APIRouter(tags=["staff-leases"])


@router.get("/staff/leases", response_model=ListResponse[StaffLeaseListItemOut])
def get_staff_leases(
    request: Request,
    lease_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _current_user: CurrentUser = Depends(require_staff),
):
    leases = staff_lease_service.get_all_leases(db, lease_status)
    return ListResponse(
        data=leases,
        meta=Meta(request_id=request.state.request_id, total=len(leases)),
    )


@router.patch("/leases/{lease_id}", response_model=SuccessResponse[LeaseOut])
def update_lease(
    lease_id: uuid.UUID,
    payload: LeaseEditIn,
    request: Request,
    db: Session = Depends(get_db),
    _current_user: CurrentUser = Depends(require_staff),
):
    lease = staff_lease_service.update_lease(db, lease_id, payload)
    return SuccessResponse(
        data=lease,
        message="Lease updated successfully",
        meta=Meta(request_id=request.state.request_id),
    )


@router.post("/leases/{lease_id}/activate", response_model=SuccessResponse[LeaseOut])
def activate_lease(
    lease_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    _current_user: CurrentUser = Depends(require_staff),
):
    lease = staff_lease_service.activate_lease(db, lease_id)
    return SuccessResponse(
        data=lease,
        message="Lease activated successfully",
        meta=Meta(request_id=request.state.request_id),
    )


@router.post("/leases/{lease_id}/renew", response_model=SuccessResponse[LeaseOut])
def renew_lease(
    lease_id: uuid.UUID,
    payload: LeaseRenewIn,
    request: Request,
    db: Session = Depends(get_db),
    _current_user: CurrentUser = Depends(require_staff),
):
    lease = staff_lease_service.renew_lease(db, lease_id, payload.new_end_date)
    return SuccessResponse(
        data=lease,
        message="Lease renewed successfully",
        meta=Meta(request_id=request.state.request_id),
    )


@router.post("/leases/{lease_id}/terminate", response_model=SuccessResponse[LeaseOut])
def terminate_lease(
    lease_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    _current_user: CurrentUser = Depends(require_staff),
):
    lease = staff_lease_service.terminate_lease(db, lease_id)
    return SuccessResponse(
        data=lease,
        message="Lease terminated successfully",
        meta=Meta(request_id=request.state.request_id),
    )


# --- AI-Generated Lease Agreement workflow (additive, staff-only) -----------


@router.post("/leases/{lease_id}/generate-agreement", response_model=SuccessResponse[AgreementDocumentOut], status_code=201)
def generate_lease_agreement(
    lease_id: uuid.UUID,
    payload: GenerateAgreementIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    lease = agreement_service.get_authorized_lease(db, lease_id, current_user)
    document = agreement_service.generate_agreement(db, lease, payload, current_user)
    return SuccessResponse(
        data=document,
        message="AI-generated draft created - review before sending",
        meta=Meta(request_id=request.state.request_id),
    )


@router.put("/leases/{lease_id}/agreement-document", response_model=SuccessResponse[AgreementDocumentOut])
def update_agreement_document(
    lease_id: uuid.UUID,
    payload: AgreementUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    lease = agreement_service.get_authorized_lease(db, lease_id, current_user)
    document = agreement_service.update_draft(db, lease, payload.content)
    return SuccessResponse(data=document, message="Draft updated", meta=Meta(request_id=request.state.request_id))


@router.post("/leases/{lease_id}/agreement-document/send", response_model=SuccessResponse[AgreementDocumentOut])
def send_agreement_document(
    lease_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    lease = agreement_service.get_authorized_lease(db, lease_id, current_user)
    document = agreement_service.send_agreement(db, lease)
    return SuccessResponse(data=document, message="Agreement sent to resident", meta=Meta(request_id=request.state.request_id))


@router.post("/leases/{lease_id}/enquiries/{enquiry_id}/respond", response_model=SuccessResponse[EnquiryOut])
def respond_to_lease_enquiry(
    lease_id: uuid.UUID,
    enquiry_id: uuid.UUID,
    payload: EnquiryRespondIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_staff),
):
    lease = agreement_service.get_authorized_lease(db, lease_id, current_user)
    enquiry = agreement_service.respond_to_enquiry(db, lease, enquiry_id, payload)
    return SuccessResponse(data=enquiry, message="Response sent", meta=Meta(request_id=request.state.request_id))
