from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.ai.invoice_insight_agent import InvoiceInsightResult, generate_ai_insight
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


def _mark_overdue_invoices(db: Session, guest_id: UUID | None, role: str) -> int:
    """Flip pending invoices past their due date to overdue (Design Contract §18/§21)."""
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
    """Staff/automation entry point for the UiPath monthly overdue-flagging step."""
    if role not in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    return _mark_overdue_invoices(db, None, role)


def _build_invoice_query(
    guest_id: UUID,
    role: str,
    lease_id: UUID | None = None,
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
    guest_id: UUID,
    role: str,
    lease_id: UUID | None = None,
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
    items = db.execute(
        query.order_by(RecurringInvoice.due_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()
    return items, total


def list_invoices_for_export(
    db: Session,
    guest_id: UUID,
    role: str,
    lease_id: UUID | None = None,
    payment_status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Unpaginated, PDF-ready invoice list with lease/unit context preloaded."""
    _mark_overdue_invoices(db, guest_id, role)
    query = _build_invoice_query(guest_id, role, lease_id, payment_status, date_from, date_to).options(
        selectinload(RecurringInvoice.lease).selectinload(LeaseAgreement.unit),
        selectinload(RecurringInvoice.lease).selectinload(LeaseAgreement.guest),
    )
    return db.execute(query.order_by(RecurringInvoice.due_date.desc())).scalars().all()


def get_invoice_insights(db: Session, guest_id: UUID, role: str, lease_id: UUID | None = None) -> InvoiceInsightResult:
    if lease_id is not None:
        lease = db.get(LeaseAgreement, lease_id)
        if lease is None:
            raise InvoiceNotFoundError("Lease not found")
        _assert_lease_access(lease, guest_id, role)

    _mark_overdue_invoices(db, guest_id, role)
    query = _build_invoice_query(guest_id, role, lease_id)
    invoices = db.execute(query.order_by(RecurringInvoice.due_date.asc())).scalars().all()
    return generate_ai_insight(invoices)


def get_invoice(db: Session, invoice_id: UUID, guest_id: UUID, role: str):
    row = db.execute(
        select(RecurringInvoice, LeaseAgreement).join(LeaseAgreement).where(RecurringInvoice.id == invoice_id)
    ).first()
    if row is None:
        raise InvoiceNotFoundError()
    invoice, lease = row
    _assert_lease_access(lease, guest_id, role)
    return invoice


def get_invoice_with_lease(db: Session, invoice_id: UUID, guest_id: UUID, role: str):
    """Loads the invoice plus lease/unit/guest context, used to render the single-invoice PDF."""
    _mark_overdue_invoices(db, guest_id, role)
    invoice = db.execute(
        select(RecurringInvoice)
        .where(RecurringInvoice.id == invoice_id)
        .options(
            selectinload(RecurringInvoice.lease).selectinload(LeaseAgreement.unit),
            selectinload(RecurringInvoice.lease).selectinload(LeaseAgreement.guest),
        )
    ).scalar_one_or_none()
    if invoice is None:
        raise InvoiceNotFoundError()
    _assert_lease_access(invoice.lease, guest_id, role)
    return invoice, invoice.lease


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
    billing_period_start = billing_period_start.replace(day=1)
    if role not in ("staff", "admin"):
        due_date = billing_period_start + timedelta(days=10)
    billing_period_end = due_date - timedelta(days=1)

    lease = db.execute(
        select(LeaseAgreement).where(LeaseAgreement.id == lease_id).with_for_update()
    ).scalar_one_or_none()
    if lease is None:
        raise InvoiceNotFoundError("Lease not found")
    _assert_lease_access(lease, guest_id, role)
    if lease.status != "active":
        raise LeaseNotEligibleError("Only active leases are eligible for invoice generation")
    if due_date <= billing_period_start:
        raise ValueError("Due date must be after the billing period start")

    existing = db.scalar(
        select(RecurringInvoice).where(
            RecurringInvoice.lease_id == lease_id,
            RecurringInvoice.billing_period_start == billing_period_start,
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
    billing_period_start = payload.billing_period_start.replace(day=1)
    due_date = payload.due_date
    if due_date <= billing_period_start:
        raise ValueError("Due date must be after the billing period start")
    billing_period_end = due_date - timedelta(days=1)
    leases = db.scalars(select(LeaseAgreement).where(LeaseAgreement.status == "active").with_for_update()).all()
    generated_ids = []
    duplicate_count = 0
    failed_count = 0
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
        )
        db.add(invoice)
        db.flush()
        generated_ids.append(invoice.id)
    db.commit()
    return generated_ids, duplicate_count, failed_count


def extend_due_date(db: Session, invoice_id: UUID, due_date: date, guest_id: UUID, role: str):
    if role not in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    invoice = get_invoice(db, invoice_id, guest_id, role)
    if due_date <= invoice.due_date:
        raise ValueError("The extended due date must be later than the current due date")
    if due_date <= invoice.billing_period_start:
        raise ValueError("Due date must be after the billing period start")
    invoice.due_date = due_date
    invoice.billing_period_end = due_date - timedelta(days=1)
    db.commit()
    db.refresh(invoice)
    return invoice


def update_payment_status(db: Session, invoice_id: UUID, payment_status: str, guest_id: UUID, role: str):
    invoice = get_invoice(db, invoice_id, guest_id, role)
    if role not in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    if payment_status not in ("paid", "overdue"):
        raise ValueError("Staff can approve payments or mark invoices overdue")
    invoice.payment_status = payment_status
    invoice.paid_at = datetime.now(timezone.utc) if payment_status == "paid" else None
    db.commit()
    db.refresh(invoice)
    return invoice


def submit_payment(db: Session, invoice_id: UUID, guest_id: UUID, role: str):
    invoice = get_invoice(db, invoice_id, guest_id, role)
    if role in ("staff", "admin"):
        raise InvoiceAccessDeniedError()
    if invoice.payment_status not in ("pending", "overdue"):
        raise ValueError("Only pending or overdue invoices can be paid")
    invoice.payment_status = "payment_submitted"
    invoice.paid_at = None
    invoice.sent_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(invoice)
    return invoice
