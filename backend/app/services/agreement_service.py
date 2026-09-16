"""
Business logic for the AI-Generated Lease Agreement workflow.

Owns AgreementDocument and LeaseEnquiry. Every function here takes an
already-loaded, already-authorized `lease` (see `get_authorized_lease`) -
the router layer resolves and authorizes it first, exactly once per
request, so a bad lease_id or a resident hitting someone else's lease
always 404s before any agreement logic runs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.lease_agreement_agent import generate_agreement_draft
from app.core.security import CurrentUser, authorize_lease_access
from app.models.agreement_document import AgreementDocument
from app.models.lease_agreement import LeaseAgreement
from app.models.lease_enquiry import LeaseEnquiry
from app.schemas.agreement import EnquiryCreateIn, EnquiryRespondIn, GenerateAgreementIn

DEFAULT_PAYMENT_DUE_DAY = 10
DEFAULT_NOTICE_PERIOD_DAYS = 60
DEFAULT_MAINTENANCE_RESPONSIBILITY = (
    "Management maintains structural and building systems; Resident agrees to "
    "report issues promptly through the property's maintenance request system."
)
DEFAULT_UTILITIES_RESPONSIBILITY = (
    "Resident is responsible for electricity, water, and internet/cable unless "
    "otherwise stated by Management."
)
# Matches the canonical policy facts already seeded for the AI Assistant
# feature (backend/documents/building_policies/, lease_terms/) so the two
# AI features never contradict each other.
DEFAULT_OCCUPANCY_TERMS = (
    "Quiet hours are observed from 10:00 PM to 7:00 AM daily. Pets are permitted "
    "with prior written approval from Management. Parking for one standard "
    "passenger vehicle is included."
)
DEFAULT_LATE_PAYMENT_TERMS = (
    "A late fee of 2% of the monthly rent applies if payment is not received "
    "within 5 days of the due date."
)
DEFAULT_RENEWAL_TERMS = (
    "This lease renews automatically for a further 12-month term unless either "
    "party provides written notice of non-renewal at least 30 days before the "
    "renewal date."
)


def get_authorized_lease(db: Session, lease_id: uuid.UUID, current_user: CurrentUser) -> LeaseAgreement:
    lease = db.get(LeaseAgreement, lease_id)
    authorize_lease_access(lease, current_user)  # raises 404 on missing/not-yours
    return lease


def _get_latest_document(db: Session, lease_id: uuid.UUID) -> AgreementDocument | None:
    return (
        db.execute(
            select(AgreementDocument).where(AgreementDocument.lease_id == lease_id).order_by(AgreementDocument.version.desc())
        )
        .scalars()
        .first()
    )


def _format_money(value: Decimal) -> str:
    return f"Rs. {value:,.2f}"


def generate_agreement(
    db: Session, lease: LeaseAgreement, payload: GenerateAgreementIn, staff_user: CurrentUser
) -> AgreementDocument:
    if lease.status not in ("pending", "active"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "LEASE_NOT_ELIGIBLE",
                "message": "Only pending or active leases can have an agreement generated.",
            },
        )

    previous = _get_latest_document(db, lease.id)
    next_version = (previous.version + 1) if previous else 1

    # Never silently overwrite an already-sent version - a regeneration
    # (e.g. after an enquiry) supersedes it instead.
    if previous is not None and previous.status in ("draft", "sent_to_resident"):
        previous.status = "superseded"
        previous.updated_at = datetime.now(timezone.utc)

    structured_fields = {
        "security_deposit": str(payload.security_deposit),
        "payment_due_day": payload.payment_due_day or DEFAULT_PAYMENT_DUE_DAY,
        "notice_period_days": payload.notice_period_days or DEFAULT_NOTICE_PERIOD_DAYS,
        "maintenance_responsibility": payload.maintenance_responsibility or DEFAULT_MAINTENANCE_RESPONSIBILITY,
        "utilities_responsibility": payload.utilities_responsibility or DEFAULT_UTILITIES_RESPONSIBILITY,
        "occupancy_terms": payload.occupancy_terms or DEFAULT_OCCUPANCY_TERMS,
        "late_payment_terms": payload.late_payment_terms or DEFAULT_LATE_PAYMENT_TERMS,
        "renewal_terms": payload.renewal_terms or DEFAULT_RENEWAL_TERMS,
    }

    context = {
        "management_name": lease.unit.property.brand or lease.unit.property.name,
        "property_name": lease.unit.property.name,
        "property_address": lease.unit.property.address,
        "resident_name": lease.guest.name,
        "unit_number": lease.unit.unit_number,
        "unit_type": lease.unit.unit_type,
        "start_date": lease.start_date.isoformat(),
        "end_date": lease.end_date.isoformat(),
        "monthly_rate": _format_money(lease.monthly_rate),
        "security_deposit": _format_money(payload.security_deposit),
        **structured_fields,
    }

    content = generate_agreement_draft(context)
    now = datetime.now(timezone.utc)

    document = AgreementDocument(
        lease_id=lease.id,
        guest_id=lease.guest_id,
        version=next_version,
        status="draft",
        content=content,
        structured_fields=structured_fields,
        generated_by_guest_id=staff_user.guest_id,
        generated_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_current_agreement_for_role(
    db: Session, lease: LeaseAgreement, current_user: CurrentUser
) -> AgreementDocument | None:
    latest = _get_latest_document(db, lease.id)
    if latest is None:
        return None
    if current_user.role in ("staff", "admin"):
        return latest
    # Residents never see a draft that hasn't been sent to them yet.
    return latest if latest.status != "draft" else None


def _get_draft_or_409(db: Session, lease: LeaseAgreement) -> AgreementDocument:
    latest = _get_latest_document(db, lease.id)
    if latest is None or latest.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "NO_DRAFT", "message": "There is no draft agreement to update."},
        )
    return latest


def update_draft(db: Session, lease: LeaseAgreement, content: str) -> AgreementDocument:
    document = _get_draft_or_409(db, lease)
    document.content = content
    document.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(document)
    return document


def send_agreement(db: Session, lease: LeaseAgreement) -> AgreementDocument:
    document = _get_draft_or_409(db, lease)
    now = datetime.now(timezone.utc)
    document.status = "sent_to_resident"
    document.sent_at = now
    document.updated_at = now
    db.commit()
    db.refresh(document)
    return document


def accept_agreement(db: Session, lease: LeaseAgreement, current_user: CurrentUser) -> AgreementDocument:
    latest = _get_latest_document(db, lease.id)
    if latest is None or latest.status != "sent_to_resident":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "NOT_ACCEPTABLE", "message": "There is no agreement awaiting your acceptance."},
        )
    now = datetime.now(timezone.utc)
    latest.status = "accepted"
    latest.accepted_at = now
    latest.accepted_by_guest_id = current_user.guest_id
    latest.updated_at = now
    db.commit()
    db.refresh(latest)
    return latest


def _get_actionable_agreement_or_404(db: Session, lease: LeaseAgreement) -> AgreementDocument:
    latest = _get_latest_document(db, lease.id)
    if latest is None or latest.status == "draft":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "AGREEMENT_NOT_FOUND", "message": "No agreement has been sent for this lease yet."},
        )
    return latest


def create_enquiry(
    db: Session, lease: LeaseAgreement, current_user: CurrentUser, payload: EnquiryCreateIn
) -> LeaseEnquiry:
    # The agreement being asked about is always resolved server-side from
    # the lease's current sent/accepted version - never trusted from the client.
    agreement = _get_actionable_agreement_or_404(db, lease)
    now = datetime.now(timezone.utc)
    enquiry = LeaseEnquiry(
        lease_id=lease.id,
        agreement_id=agreement.id,
        guest_id=current_user.guest_id,
        subject=payload.subject,
        message=payload.message,
        reference=payload.reference,
        status="open",
        created_at=now,
    )
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)
    return enquiry


def list_enquiries(db: Session, lease: LeaseAgreement) -> list[LeaseEnquiry]:
    return (
        db.execute(select(LeaseEnquiry).where(LeaseEnquiry.lease_id == lease.id).order_by(LeaseEnquiry.created_at.desc()))
        .scalars()
        .all()
    )


def _get_enquiry_or_404(db: Session, lease: LeaseAgreement, enquiry_id: uuid.UUID) -> LeaseEnquiry:
    enquiry = db.get(LeaseEnquiry, enquiry_id)
    if enquiry is None or enquiry.lease_id != lease.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ENQUIRY_NOT_FOUND", "message": "Enquiry not found."},
        )
    return enquiry


def respond_to_enquiry(
    db: Session, lease: LeaseAgreement, enquiry_id: uuid.UUID, payload: EnquiryRespondIn
) -> LeaseEnquiry:
    enquiry = _get_enquiry_or_404(db, lease, enquiry_id)
    now = datetime.now(timezone.utc)
    enquiry.staff_response = payload.response
    enquiry.responded_at = now
    enquiry.status = "closed" if payload.close else "answered"
    if payload.close:
        enquiry.closed_at = now
    db.commit()
    db.refresh(enquiry)
    return enquiry
