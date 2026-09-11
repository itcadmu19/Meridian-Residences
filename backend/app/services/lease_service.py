from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.guest import Guest
from app.models.lease_agreement import LeaseAgreement
from app.models.maintenance_ticket import MaintenanceTicket
from app.models.property import Property
from app.models.recurring_invoice import RecurringInvoice
from app.models.unit import Unit


class LeaseNotFoundError(Exception):
    pass


class LeaseAccessDeniedError(Exception):
    pass


def _lease_query():
    return (
        select(LeaseAgreement, Unit.unit_number, Unit.unit_type, Property.name, Guest.name, Guest.email)
        .join(Unit, LeaseAgreement.unit_id == Unit.id)
        .join(Property, Unit.property_id == Property.id)
        .join(Guest, LeaseAgreement.guest_id == Guest.id)
    )


def _lease_record(row):
    lease, unit_number, unit_type, property_name, guest_name, guest_email = row
    return lease, {
        "unit_number": unit_number,
        "unit_type": unit_type,
        "property_name": property_name,
        "guest_name": guest_name,
        "guest_email": guest_email,
    }


def get_lease(db: Session, lease_id: UUID, guest_id: UUID, role: str):
    row = db.execute(_lease_query().where(LeaseAgreement.id == lease_id)).first()
    if row is None:
        raise LeaseNotFoundError()
    lease, details = _lease_record(row)
    if role not in ("staff", "admin") and lease.guest_id != guest_id:
        raise LeaseAccessDeniedError()
    return lease, details


def get_guest_leases(db: Session, guest_id: UUID, role: str):
    query = _lease_query()
    if role not in ("staff", "admin"):
        query = query.where(LeaseAgreement.guest_id == guest_id)
    rows = db.execute(query.order_by(LeaseAgreement.start_date.desc())).all()
    return [_lease_record(row) for row in rows]


def get_summary(db: Session, lease_id: UUID, guest_id: UUID, role: str):
    lease, details = get_lease(db, lease_id, guest_id, role)
    outstanding_amount = db.scalar(
        select(func.coalesce(func.sum(RecurringInvoice.amount), 0)).where(
            RecurringInvoice.lease_id == lease.id,
            RecurringInvoice.payment_status.in_(["pending", "overdue"]),
        )
    )
    upcoming_invoice_count = db.scalar(
        select(func.count(RecurringInvoice.id)).where(
            RecurringInvoice.lease_id == lease.id,
            RecurringInvoice.payment_status == "pending",
        )
    )
    open_maintenance_count = db.scalar(
        select(func.count(MaintenanceTicket.id)).where(
            MaintenanceTicket.guest_id == lease.guest_id,
            MaintenanceTicket.status.in_(["open", "assigned", "in_progress"]),
        )
    )
    return lease, details, {
        "upcoming_invoice_count": upcoming_invoice_count or 0,
        "outstanding_amount": outstanding_amount or 0,
        "open_maintenance_count": open_maintenance_count or 0,
    }
