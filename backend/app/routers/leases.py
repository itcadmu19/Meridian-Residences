"""
HTTP layer for User Story 1 - View Lease Details.

The three GET endpoints below are frozen (Project Design Document section
9.2 / 17) - no renaming those or adding contract-breaking siblings. The
`/agreement` and `/renewal-request` endpoints are additive: they extend
this story's own router/table, touch no other member's data, and were
added after the base story was working (see the story-extension plan for
Download Agreement / Request Renewal). No business logic here - see
app/services/lease_service.py for that.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_guest_id, require_resident
from app.schemas.agreement import AgreementDocumentOut, EnquiryCreateIn, EnquiryOut
from app.schemas.common import ListResponse, Meta, SuccessResponse
from app.schemas.lease import LeaseListItemOut, LeaseOut, LeaseSummaryOut, RenewalRequestOut
from app.services import agreement_service, lease_service
from app.services.agreement_document_pdf import generate_agreement_document_pdf

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


@router.get("/leases/{lease_id}/agreement")
def download_lease_agreement(
    lease_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    """Deliberate exception to the response envelope: a successful download
    returns raw PDF bytes, not {success, data, message, meta} - binary
    content can't be wrapped in JSON. Every error path still uses the
    standard envelope via the shared exception handlers in main.py."""
    pdf_bytes = lease_service.get_lease_agreement_pdf(db, lease_id, current_user)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="lease_agreement_{lease_id}.pdf"'},
    )


@router.post("/leases/{lease_id}/renewal-request", response_model=SuccessResponse[RenewalRequestOut])
def request_lease_renewal(
    lease_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    result = lease_service.request_lease_renewal(db, lease_id, current_user)
    return SuccessResponse(
        data=result,
        message="Renewal already requested" if result.already_requested else "Renewal requested successfully",
        meta=Meta(request_id=request.state.request_id),
    )


# --- AI-Generated Lease Agreement workflow (additive) -----------------------
# Deliberately NOT "/leases/{lease_id}/agreement" - that path is already the
# frozen contract's PDF download above. This is a different resource (the
# generated/reviewed agreement document, versioned), hence "agreement-document".


@router.get("/leases/{lease_id}/agreement-document", response_model=SuccessResponse[AgreementDocumentOut | None])
def get_agreement_document(
    lease_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    lease = agreement_service.get_authorized_lease(db, lease_id, current_user)
    document = agreement_service.get_current_agreement_for_role(db, lease, current_user)
    return SuccessResponse(data=document, meta=Meta(request_id=request.state.request_id))


@router.get("/leases/{lease_id}/agreement-document/pdf")
def download_agreement_document_pdf(
    lease_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    lease = agreement_service.get_authorized_lease(db, lease_id, current_user)
    document = agreement_service.get_current_agreement_for_role(db, lease, current_user)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "AGREEMENT_NOT_FOUND", "message": "No agreement is available for this lease yet."},
        )
    pdf_bytes = generate_agreement_document_pdf(document, lease)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="agreement_{lease_id}_v{document.version}.pdf"'},
    )


@router.post("/leases/{lease_id}/agreement-document/accept", response_model=SuccessResponse[AgreementDocumentOut])
def accept_agreement_document(
    lease_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_resident),
):
    lease = agreement_service.get_authorized_lease(db, lease_id, current_user)
    document = agreement_service.accept_agreement(db, lease, current_user)
    return SuccessResponse(data=document, message="Lease agreement accepted", meta=Meta(request_id=request.state.request_id))


@router.get("/leases/{lease_id}/enquiries", response_model=ListResponse[EnquiryOut])
def get_lease_enquiries(
    lease_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_guest_id),
):
    lease = agreement_service.get_authorized_lease(db, lease_id, current_user)
    enquiries = agreement_service.list_enquiries(db, lease)
    return ListResponse(data=enquiries, meta=Meta(request_id=request.state.request_id, total=len(enquiries)))


@router.post("/leases/{lease_id}/enquiries", response_model=SuccessResponse[EnquiryOut], status_code=201)
def create_lease_enquiry(
    lease_id: uuid.UUID,
    payload: EnquiryCreateIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_resident),
):
    lease = agreement_service.get_authorized_lease(db, lease_id, current_user)
    enquiry = agreement_service.create_enquiry(db, lease, current_user, payload)
    return SuccessResponse(data=enquiry, message="Enquiry submitted", meta=Meta(request_id=request.state.request_id))
