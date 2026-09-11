from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lease_agreement import LeaseAgreement
from app.models.recurring_invoice import RecurringInvoice


class InvoiceNotFoundError(Exception):
    pass


class InvoiceAccessDeniedError(Exception):
    pass


class LeaseNotEligibleError(Exception):
    pass


def _assert_lease_access(lease: LeaseAgreement, guest_id: UUID, role: str):
    if role not in ("staff", "admin") and lease.guest_id != guest_id:
        raise InvoiceAccessDeniedError()


def list_invoices(
    db: Session,
    guest_id: UUID,
    role: str,
    lease_id: UUID | None = None,
    payment_status: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(RecurringInvoice).join(LeaseAgreement)
    if role not in ("staff", "admin"):
        query = query.where(LeaseAgreement.guest_id == guest_id)
    if lease_id is not None:
        query = query.where(RecurringInvoice.lease_id == lease_id)
    if payment_status is not None:
        query = query.where(RecurringInvoice.payment_status == payment_status)

    total = len(db.execute(query).scalars().all())
    page_size = min(max(page_size, 1), 100)
    page = max(page, 1)
    items = db.execute(
        query.order_by(RecurringInvoice.due_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    return items, total


def get_invoice(db: Session, invoice_id: UUID, guest_id: UUID, role: str):
    row = db.execute(
        select(RecurringInvoice, LeaseAgreement).join(LeaseAgreement).where(RecurringInvoice.id == invoice_id)
    ).first()
    if row is None:
        raise InvoiceNotFoundError()
    invoice, lease = row
    _assert_lease_access(lease, guest_id, role)
    return invoice


def generate_invoice(
    db: Session,
    guest_id: UUID,
    role: str,
    lease_id: UUID,
    billing_period_start: date,
    billing_period_end: date,
    due_date: date,
    amount: Decimal | None = None,
):
    lease = db.execute(
        select(LeaseAgreement).where(LeaseAgreement.id == lease_id).with_for_update()
    ).scalar_one_or_none()
    if lease is None:
        raise InvoiceNotFoundError("Lease not found")
    _assert_lease_access(lease, guest_id, role)
    if lease.status != "active":
        raise LeaseNotEligibleError("Only active leases are eligible for invoice generation")
    if billing_period_end < billing_period_start:
        raise ValueError("Billing period end must be on or after the start")

    existing = db.scalar(
        select(RecurringInvoice).where(
            RecurringInvoice.lease_id == lease_id,
            RecurringInvoice.billing_period_start == billing_period_start,
            RecurringInvoice.billing_period_end == billing_period_end,
        )
    )
    if existing is not None:
        return existing, False

    invoice = RecurringInvoice(
        lease_id=lease_id,
        billing_period_start=billing_period_start,
        billing_period_end=billing_period_end,
        amount=amount or lease.monthly_rate,
        due_date=due_date,
        payment_status="pending",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice, True


def generate_batch(db: Session, payload, role: str):
    if role not in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    leases = db.scalars(select(LeaseAgreement).where(LeaseAgreement.status == "active").with_for_update()).all()
    generated_ids = []
    duplicate_count = 0
    failed_count = 0
    for lease in leases:
        existing = db.scalar(
            select(RecurringInvoice).where(
                RecurringInvoice.lease_id == lease.id,
                RecurringInvoice.billing_period_start == payload.billing_period_start,
                RecurringInvoice.billing_period_end == payload.billing_period_end,
            )
        )
        if existing is not None:
            duplicate_count += 1
            generated_ids.append(existing.id)
            continue
        invoice = RecurringInvoice(
            lease_id=lease.id,
            billing_period_start=payload.billing_period_start,
            billing_period_end=payload.billing_period_end,
            amount=lease.monthly_rate,
            due_date=payload.due_date,
            payment_status="pending",
        )
        db.add(invoice)
        db.flush()
        generated_ids.append(invoice.id)
    db.commit()
    return generated_ids, duplicate_count, failed_count


def update_payment_status(db: Session, invoice_id: UUID, payment_status: str, guest_id: UUID, role: str):
    invoice = get_invoice(db, invoice_id, guest_id, role)
    invoice.payment_status = payment_status
    invoice.paid_at = datetime.now(timezone.utc) if payment_status == "paid" else None
    db.commit()
    db.refresh(invoice)
    return invoice
