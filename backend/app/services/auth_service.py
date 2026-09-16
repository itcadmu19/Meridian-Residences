"""
Login business logic - ported from teammate feature-lavanya's branch,
adapted to this branch's JWT helper (create_access_token in
core/security.py) instead of PyJWT's raw encode.

`register()` is the self-service Registration feature, ported from a newer
copy of her branch - adapted to this app's explicit created_at convention
(her models use Postgres server_default=func.now(); ours don't) and
GUID()-typed FKs.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.lease_agreement_agent import generate_agreement_draft
from app.core.security import create_access_token, hash_password, verify_password
from app.models.agreement_document import AgreementDocument
from app.models.guest import Guest
from app.models.lease_agreement import LeaseAgreement
from app.models.property import Property
from app.models.recurring_invoice import RecurringInvoice
from app.models.resident_credential import ResidentCredential
from app.models.unit import Unit
from app.schemas.auth import RegisterRequest, RegisterResponse, TokenResponse
from app.services import agreement_service
from app.services.invoice_service import _billing_period_bounds

logger = logging.getLogger(__name__)

# New resident self-registrations get a real, populated account immediately
# - lease, AI lease agreement, and first invoice - since there is no
# separate "assign a lease"/"generate agreement"/"generate invoice" flow a
# human would otherwise run for them, and an empty Dashboard/Lease page
# looks like the app is broken rather than "you just signed up". Rate
# defaults roughly match database/seed/seed_lease_story.py's existing demo
# leases (42000-47000) so a new account looks consistent with the seeded
# ones, not arbitrary.
_DEFAULT_MONTHLY_RATE_BY_UNIT_TYPE = {
    "studio": Decimal("32000.00"),
    "1bhk": Decimal("38000.00"),
    "2bhk": Decimal("45000.00"),
    "3bhk": Decimal("55000.00"),
}
_DEFAULT_LEASE_TERM_DAYS = 365
_DEFAULT_RENEWAL_WINDOW_DAYS = 30


def _default_monthly_rate(unit_type: str | None) -> Decimal:
    key = (unit_type or "").strip().lower()
    return _DEFAULT_MONTHLY_RATE_BY_UNIT_TYPE.get(key, Decimal("45000.00"))


def _next_unit_number(db: Session, property_row: Property) -> str:
    """A resident who doesn't type a unit number at signup used to always
    land in the same hardcoded "101" - harmless with one seeded account,
    but every such signup piled another *simultaneously active* lease onto
    that one unit, which made Staff Lease Management look like a data bug
    (a dozen different "current" tenants in the same apartment). Auto-
    assign the next free numeric unit instead, continuing from whatever's
    already in use for this property."""
    existing_numbers = [
        row[0] for row in db.query(Unit.unit_number).filter(Unit.property_id == property_row.id).all()
    ]
    numeric_values = []
    for value in existing_numbers:
        try:
            numeric_values.append(int(value))
        except (TypeError, ValueError):
            continue
    next_number = (max(numeric_values) + 1) if numeric_values else 101
    return str(next_number)


def _ensure_active_lease(db: Session, guest: Guest, unit: Unit, now: datetime) -> LeaseAgreement:
    existing = db.query(LeaseAgreement).filter(LeaseAgreement.guest_id == guest.id).first()
    if existing is not None:
        return existing

    start_date = now.date()
    end_date = start_date + timedelta(days=_DEFAULT_LEASE_TERM_DAYS)
    lease = LeaseAgreement(
        unit_id=unit.id,
        guest_id=guest.id,
        start_date=start_date,
        end_date=end_date,
        monthly_rate=_default_monthly_rate(unit.unit_type),
        renewal_date=end_date - timedelta(days=_DEFAULT_RENEWAL_WINDOW_DAYS),
        status="active",
        # Marker only (see lease_agreement_pdf.py's docstring) - the PDF is
        # rendered on demand from the lease's own fields, nothing is read
        # from this path. Matches database/seed/seed_lease_story.py's
        # AGREEMENT_AVAILABLE convention for active leases, so the existing
        # "Download agreement" button on the Lease page works for a new
        # signup exactly like it does for a seeded demo resident.
        agreement_file_url="generated",
        created_at=now,
        updated_at=now,
    )
    db.add(lease)
    db.flush()
    return lease


def _format_money(value: Decimal) -> str:
    return f"Rs. {value:,.2f}"


def _ensure_agreement_document(
    db: Session, lease: LeaseAgreement, guest: Guest, unit: Unit, property_row: Property, now: datetime
) -> None:
    """Bootstrap-only exception: everywhere else (agreement_service.py,
    the staff-facing generate/send endpoints) an AI-generated agreement is
    always created as a `draft` and requires an explicit staff "send"
    action - that review step is a deliberate legal-safety requirement, not
    a formality, and stays enforced there. This helper only runs once, at
    self-registration, when there is no staff in the loop at all (the
    resident *is* the only party present) - it generates the same
    deterministic-template draft and marks it sent so the account isn't
    empty, but does not touch or bypass the staff review path itself."""
    existing = db.query(AgreementDocument).filter(AgreementDocument.lease_id == lease.id).first()
    if existing is not None:
        return

    security_deposit = lease.monthly_rate
    structured_fields = {
        "security_deposit": _format_money(security_deposit),
        "payment_due_day": agreement_service.DEFAULT_PAYMENT_DUE_DAY,
        "notice_period_days": agreement_service.DEFAULT_NOTICE_PERIOD_DAYS,
        "maintenance_responsibility": agreement_service.DEFAULT_MAINTENANCE_RESPONSIBILITY,
        "utilities_responsibility": agreement_service.DEFAULT_UTILITIES_RESPONSIBILITY,
        "occupancy_terms": agreement_service.DEFAULT_OCCUPANCY_TERMS,
        "late_payment_terms": agreement_service.DEFAULT_LATE_PAYMENT_TERMS,
        "renewal_terms": agreement_service.DEFAULT_RENEWAL_TERMS,
    }
    context = {
        "management_name": property_row.brand or property_row.name,
        "property_name": property_row.name,
        "property_address": property_row.address,
        "resident_name": guest.name,
        "unit_number": unit.unit_number,
        "unit_type": unit.unit_type,
        "start_date": lease.start_date.isoformat(),
        "end_date": lease.end_date.isoformat(),
        "monthly_rate": _format_money(lease.monthly_rate),
        **structured_fields,
    }

    document = AgreementDocument(
        lease_id=lease.id,
        guest_id=guest.id,
        version=1,
        status="sent_to_resident",
        content=generate_agreement_draft(context),
        structured_fields=structured_fields,
        generated_by_guest_id=None,
        generated_at=now,
        sent_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(document)


def _ensure_first_invoice(db: Session, lease: LeaseAgreement, now: datetime) -> None:
    existing = db.query(RecurringInvoice).filter(RecurringInvoice.lease_id == lease.id).first()
    if existing is not None:
        return

    # Same full-calendar-month / due-the-10th-of-next-month rule as every
    # other invoice in the app - see invoice_service.py's module docstring.
    billing_start, billing_end, due_date = _billing_period_bounds(now.date())
    invoice = RecurringInvoice(
        lease_id=lease.id,
        billing_period_start=billing_start,
        billing_period_end=billing_end,
        amount=lease.monthly_rate,
        due_date=due_date,
        payment_status="pending",
        generated_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(invoice)


class InvalidCredentialsError(Exception):
    pass


class EmailAlreadyExistsError(Exception):
    pass


def _display_name_from_email(email: str) -> str:
    local = email.split("@")[0]
    parts = [part for part in re.split(r"[._-]+", local) if part]
    name = " ".join(part[:1].upper() + part[1:] for part in parts)
    return name or "New Resident"


def login(db: Session, email: str, password: str, role: str = "resident") -> TokenResponse:
    normalized_email = email.strip().lower()
    credential = (
        db.query(ResidentCredential)
        .filter(func.lower(ResidentCredential.email) == normalized_email)
        .first()
    )

    if credential is None:
        # No account with this email yet - self-service convenience: create
        # one on the spot (same provisioning as an explicit /register call,
        # including the auto lease/agreement/invoice above) rather than
        # rejecting the sign-in, so any email "just works" whether someone
        # used the Register page first or not. `role` comes from the
        # Sign In page's own role tab (resident/staff), same choice
        # Register.jsx offers - it only affects a brand-new account; an
        # existing email's stored role is never changed by this.
        # A wrong password on an email that DOES already exist is still
        # rejected below - this path only fires for a genuinely new address.
        result = register(
            db,
            RegisterRequest(
                name=_display_name_from_email(normalized_email),
                email=normalized_email,
                password=password,
                role=role if role in {"resident", "staff", "admin"} else "resident",
            ),
        )
        logger.info("Auto-created account on first sign-in for email=%s", normalized_email)
        return TokenResponse(
            access_token=result.access_token,
            guest_id=result.guest_id,
            unit_id=result.unit_id,
            role=result.role,
        )

    if not verify_password(password, credential.password_hash):
        logger.info("Failed login attempt for email=%s", normalized_email)
        raise InvalidCredentialsError("Invalid email or password")

    token = create_access_token(credential.guest_id, credential.role, credential.unit_id)
    logger.info("Successful login for guest_id=%s", credential.guest_id)

    return TokenResponse(
        access_token=token,
        guest_id=credential.guest_id,
        unit_id=credential.unit_id,
        role=credential.role,
    )


def register(db: Session, payload: RegisterRequest) -> RegisterResponse:
    normalized_email = payload.email.strip().lower()
    if db.query(ResidentCredential).filter(func.lower(ResidentCredential.email) == normalized_email).first():
        raise EmailAlreadyExistsError("An account with this email already exists")

    now = datetime.now(timezone.utc)

    role = payload.role.strip().lower() if payload.role else "resident"
    if role not in {"resident", "staff", "admin"}:
        role = "resident"

    property_name = (payload.property_name or "Meridian Residences").strip() or "Meridian Residences"
    property_row = db.query(Property).filter(func.lower(Property.name) == property_name.lower()).first()
    if property_row is None:
        property_row = Property(name=property_name, brand="Meridian", timezone="UTC")
        db.add(property_row)
        db.flush()

    explicit_unit_number = (payload.unit_number or "").strip()
    if explicit_unit_number:
        unit_number = explicit_unit_number
    elif role == "staff":
        unit_number = "STAFF-01"
    else:
        # No unit typed at signup - give this resident their own unit
        # rather than piling every default signup onto the same one.
        unit_number = _next_unit_number(db, property_row)

    unit = (
        db.query(Unit)
        .filter(Unit.property_id == property_row.id, func.lower(Unit.unit_number) == unit_number.lower())
        .first()
    )
    if unit is None:
        unit = Unit(
            property_id=property_row.id,
            unit_number=unit_number,
            unit_type=payload.unit_type or ("Staff" if role == "staff" else "2BHK"),
            status="occupied",
            created_at=now,
        )
        db.add(unit)
        db.flush()

    guest = db.query(Guest).filter(func.lower(Guest.email) == normalized_email).first()
    if guest is None:
        guest = Guest(
            name=payload.name.strip() or "New Resident",
            email=normalized_email,
            phone=None,
            loyalty_tier="silver",
            created_at=now,
        )
        db.add(guest)
        db.flush()

    if role == "resident":
        lease = _ensure_active_lease(db, guest, unit, now)
        _ensure_agreement_document(db, lease, guest, unit, property_row, now)
        _ensure_first_invoice(db, lease, now)

    credential = ResidentCredential(
        guest_id=guest.id,
        unit_id=unit.id,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=role,
        created_at=now,
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)

    token = create_access_token(credential.guest_id, credential.role, credential.unit_id)
    logger.info("Registered new %s account for guest_id=%s", role, guest.id)

    return RegisterResponse(
        access_token=token,
        guest_id=credential.guest_id,
        unit_id=credential.unit_id,
        role=credential.role,
        email=credential.email,
        name=guest.name,
    )
