"""
Invoice business logic - ported from teammate feature-lavanya's branch (same
authorization rules: resident sees/acts on invoices for their own leases
only, staff/admin see/act on all), then extended with the approve-then-pay
workflow, auto-overdue sweep, due-date extension, AI payment insight, and
PDF export ported from teammate feature-annapoorna's branch. Adapted to this
branch's explicit created_at/updated_at convention and `noload()` fix for
`with_for_update()` (see the outer-join + FOR UPDATE note on the earlier
port).

Billing period rule (business decision, supersedes both branches' own
rules - annapoorna's gave residents only a 10-day billing period, which
doesn't match how rent actually works): a generated invoice always covers
the full calendar month of `billing_period_start`, due the 10th of the
*following* month, computed server-side by `_billing_period_bounds` and
applied uniformly to both `generate_invoice` and `generate_batch` -
`billing_period_end`/`due_date` in the request are no longer read (see
schemas/invoice.py). This also fixes a real bug: the frontend's "Generate
monthly batch" call never sent `billing_period_end`, which used to be a
required field, so every batch-generate request 422'd.

`get_latest_invoice_for_lease` is additive - not part of either branch. It's
the interface `lease_service.py`'s dashboard summary already calls
defensively (see its `_next_payment_and_activity` helper) and no-ops
without; adding it wires the Dashboard's "Next Payment" card to real data.
"""

from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session, noload

from app.ai.invoice_insight_agent import InvoiceInsightResult, generate_ai_insight
from app.models.lease_agreement import LeaseAgreement
from app.models.recurring_invoice import RecurringInvoice


def _billing_period_bounds(billing_period_start: date) -> tuple[date, date, date]:
    """Full calendar month of `billing_period_start`, due the 10th of the
    following month. Returns (start, end, due_date)."""
    start = billing_period_start.replace(day=1)
    last_day = monthrange(start.year, start.month)[1]
    end = start.replace(day=last_day)
    if start.month == 12:
        due = date(start.year + 1, 1, 10)
    else:
        due = date(start.year, start.month + 1, 10)
    return start, end, due


class InvoiceNotFoundError(Exception):
    pass


class InvoiceAccessDeniedError(Exception):
    pass


class LeaseNotEligibleError(Exception):
    pass


def _assert_lease_access(lease: LeaseAgreement, guest_id: uuid.UUID, role: str) -> None:
    if role not in ("staff", "admin") and lease.guest_id != guest_id:
        raise InvoiceAccessDeniedError()


def _mark_overdue_invoices(db: Session, guest_id: uuid.UUID | None, role: str) -> int:
    """Flip pending invoices past their due date to overdue, scoped to the
    caller's own leases unless they're staff/admin."""
    query = update(RecurringInvoice).where(
        RecurringInvoice.payment_status == "pending",
        RecurringInvoice.due_date < date.today(),
    )
    if role not in ("staff", "admin"):
        query = query.where(
            RecurringInvoice.lease_id.in_(select(LeaseAgreement.id).where(LeaseAgreement.guest_id == guest_id))
        )
    result = db.execute(query.values(payment_status="overdue"))
    db.commit()
    return result.rowcount or 0


def mark_overdue_invoices(db: Session, role: str) -> int:
    """Staff-only entry point for a manual/automated overdue-flagging sweep."""
    if role not in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    return _mark_overdue_invoices(db, None, role)


def _build_invoice_query(
    guest_id: uuid.UUID,
    role: str,
    lease_id: uuid.UUID | None = None,
    payment_status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    query = select(RecurringInvoice).join(LeaseAgreement)
    if role not in ("staff", "admin"):
        query = query.where(LeaseAgreement.guest_id == guest_id)
    if lease_id is not None:
        query = query.where(RecurringInvoice.lease_id == lease_id)
    if payment_status is not None:
        query = query.where(RecurringInvoice.payment_status == payment_status)
    if date_from is not None:
        query = query.where(RecurringInvoice.due_date >= date_from)
    if date_to is not None:
        query = query.where(RecurringInvoice.due_date <= date_to)
    return query


def list_invoices(
    db: Session,
    guest_id: uuid.UUID,
    role: str,
    lease_id: uuid.UUID | None = None,
    payment_status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 20,
):
    _mark_overdue_invoices(db, guest_id, role)
    query = _build_invoice_query(guest_id, role, lease_id, payment_status, date_from, date_to)

    total = len(db.execute(query).scalars().all())
    page_size = min(max(page_size, 1), 100)
    page = max(page, 1)
    items = (
        db.execute(
            query.order_by(RecurringInvoice.due_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return items, total


def list_invoices_for_export(
    db: Session,
    guest_id: uuid.UUID,
    role: str,
    lease_id: uuid.UUID | None = None,
    payment_status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Unpaginated, PDF-ready invoice list. `RecurringInvoice.lease` and
    `LeaseAgreement.unit`/`.guest` are already `lazy="joined"` at the mapper
    level, so a plain query eager-loads everything invoice_pdf.py needs."""
    _mark_overdue_invoices(db, guest_id, role)
    query = _build_invoice_query(guest_id, role, lease_id, payment_status, date_from, date_to)
    return db.execute(query.order_by(RecurringInvoice.due_date.desc())).scalars().all()


def get_invoice_insights(db: Session, guest_id: uuid.UUID, role: str, lease_id: uuid.UUID | None = None) -> InvoiceInsightResult:
    if lease_id is not None:
        lease = db.get(LeaseAgreement, lease_id)
        if lease is None:
            raise InvoiceNotFoundError("Lease not found")
        _assert_lease_access(lease, guest_id, role)

    _mark_overdue_invoices(db, guest_id, role)
    query = _build_invoice_query(guest_id, role, lease_id)
    invoices = db.execute(query.order_by(RecurringInvoice.due_date.asc())).scalars().all()
    return generate_ai_insight(invoices, for_staff=role in ("staff", "admin"))


def get_invoice(db: Session, invoice_id: uuid.UUID, guest_id: uuid.UUID, role: str):
    row = db.execute(
        select(RecurringInvoice, LeaseAgreement)
        .join(LeaseAgreement)
        .where(RecurringInvoice.id == invoice_id)
    ).first()
    if row is None:
        raise InvoiceNotFoundError()
    invoice, lease = row
    _assert_lease_access(lease, guest_id, role)
    return invoice


def get_invoice_with_lease(db: Session, invoice_id: uuid.UUID, guest_id: uuid.UUID, role: str):
    """Loads the invoice plus lease/unit/guest context, used to render the single-invoice PDF."""
    _mark_overdue_invoices(db, guest_id, role)
    invoice = db.get(RecurringInvoice, invoice_id)
    if invoice is None:
        raise InvoiceNotFoundError()
    _assert_lease_access(invoice.lease, guest_id, role)
    return invoice, invoice.lease


def generate_invoice(
    db: Session,
    guest_id: uuid.UUID,
    role: str,
    lease_id: uuid.UUID,
    billing_period_start: date,
    billing_period_end: date,
    due_date: date,
    amount: Decimal | None = None,
):
    # billing_period_end/due_date args are accepted for signature
    # compatibility but ignored - see _billing_period_bounds.
    billing_period_start, billing_period_end, due_date = _billing_period_bounds(billing_period_start)

    lease = db.execute(
        select(LeaseAgreement)
        .where(LeaseAgreement.id == lease_id)
        .options(noload(LeaseAgreement.unit), noload(LeaseAgreement.guest))
        .with_for_update()
    ).scalar_one_or_none()
    if lease is None:
        raise InvoiceNotFoundError("Lease not found")
    _assert_lease_access(lease, guest_id, role)
    if lease.status != "active":
        raise LeaseNotEligibleError("Only active leases are eligible for invoice generation")

    # Billing period must fall within the lease term - a resident may only
    # generate invoices for months their lease actually covers, not before
    # move-in or after the agreement ends. Boundary months (lease starts or
    # ends mid-month) are still allowed since rent is still owed for them.
    if billing_period_end < lease.start_date or billing_period_start > lease.end_date:
        raise LeaseNotEligibleError(
            f"Billing period must fall within the lease term "
            f"({lease.start_date.isoformat()} to {lease.end_date.isoformat()})"
        )

    # One invoice per lease per calendar month - never generate a second
    # one for a month that already has one.
    existing = db.scalar(
        select(RecurringInvoice).where(
            RecurringInvoice.lease_id == lease_id,
            RecurringInvoice.billing_period_start == billing_period_start,
        )
    )
    if existing is not None:
        return existing, False

    now = datetime.now(timezone.utc)
    invoice = RecurringInvoice(
        lease_id=lease_id,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end,
        amount=amount or lease.monthly_rate,
        due_date=due_date,
        payment_status="pending",
        generated_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice, True


def generate_batch(db: Session, payload, role: str):
    if role not in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    billing_period_start, billing_period_end, due_date = _billing_period_bounds(payload.billing_period_start)

    leases = db.scalars(
        select(LeaseAgreement)
        .where(LeaseAgreement.status == "active")
        .options(noload(LeaseAgreement.unit), noload(LeaseAgreement.guest))
        .with_for_update()
    ).all()
    generated_ids = []
    duplicate_count = 0
    failed_count = 0
    now = datetime.now(timezone.utc)
    for lease in leases:
        existing = db.scalar(
            select(RecurringInvoice).where(
                RecurringInvoice.lease_id == lease.id,
                RecurringInvoice.billing_period_start == billing_period_start,
            )
        )
        if existing is not None:
            duplicate_count += 1
            generated_ids.append(existing.id)
            continue
        invoice = RecurringInvoice(
            lease_id=lease.id,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            amount=lease.monthly_rate,
            due_date=due_date,
            payment_status="pending",
            generated_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(invoice)
        db.flush()
        generated_ids.append(invoice.id)
    db.commit()
    return generated_ids, duplicate_count, failed_count


def extend_due_date(db: Session, invoice_id: uuid.UUID, due_date: date, guest_id: uuid.UUID, role: str):
    if role not in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    invoice = get_invoice(db, invoice_id, guest_id, role)
    if due_date <= invoice.due_date:
        raise ValueError("The extended due date must be later than the current due date")
    if due_date <= invoice.billing_period_start:
        raise ValueError("Due date must be after the billing period start")
    invoice.due_date = due_date
    invoice.billing_period_end = due_date - timedelta(days=1)
    invoice.payment_status = "due_extended"
    invoice.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invoice)
    return invoice


def update_payment_status(db: Session, invoice_id: uuid.UUID, payment_status: str, guest_id: uuid.UUID, role: str):
    invoice = get_invoice(db, invoice_id, guest_id, role)
    if role not in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    if payment_status not in ("paid", "overdue"):
        raise ValueError("Staff can approve payments or mark invoices overdue")
    invoice.payment_status = payment_status
    invoice.paid_at = datetime.now(timezone.utc) if payment_status == "paid" else None
    invoice.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invoice)
    return invoice


def submit_payment(db: Session, invoice_id: uuid.UUID, guest_id: uuid.UUID, role: str):
    """Resident-facing dummy payment submission - no real charge is made.
    Leaves the invoice at `payment_submitted` until staff approve it."""
    invoice = get_invoice(db, invoice_id, guest_id, role)
    if role in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    if invoice.payment_status not in ("pending", "overdue", "due_extended"):
        raise ValueError("Only pending, overdue, or due-extended invoices can be paid")
    invoice.payment_status = "payment_submitted"
    invoice.paid_at = None
    invoice.sent_at = datetime.now(timezone.utc)
    invoice.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_latest_invoice_for_lease(lease_id: uuid.UUID):
    """Dashboard adapter (additive) - see module docstring. Prefers the
    soonest-due unpaid invoice ("next payment"); falls back to the most
    recently generated invoice if everything is already settled."""
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        pending = db.scalar(
            select(RecurringInvoice)
            .where(
                RecurringInvoice.lease_id == lease_id,
                RecurringInvoice.payment_status.in_(("pending", "overdue", "due_extended")),
            )
            .order_by(RecurringInvoice.due_date.asc())
        )
        if pending is not None:
            return pending
        return db.scalar(
            select(RecurringInvoice)
            .where(RecurringInvoice.lease_id == lease_id)
            .order_by(RecurringInvoice.due_date.desc())
        )
    finally:
        db.close()
