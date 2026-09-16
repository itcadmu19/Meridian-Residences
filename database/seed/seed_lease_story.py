"""
Seed data for User Story 1 - View Lease Details.

Uses the logical seed IDs from the Project Design Document section 22
(GUEST-001, PROP-001, UNIT-101, LEASE-001) as deterministic UUIDs (derived
via uuid5) so every developer gets the same IDs locally without needing to
share a database dump. Run from backend/ with the venv active and
DATABASE_URL set, e.g.:

    DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/meridian_residences \
        python ../database/seed/seed_lease_story.py

Idempotency is per-record (checked by deterministic UUID individually),
not a single global short-circuit - re-running this script after new
leases are added below will insert only what's missing, without
duplicating anything already seeded. This matters because other team
members may already have LEASE-001 seeded locally and still need
LEASE-002/003/004 to appear on a re-run.
"""

import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.guest import Guest  # noqa: E402
from app.models.lease_agreement import LeaseAgreement  # noqa: E402
from app.models.maintenance_ticket import MaintenanceTicket  # noqa: E402
from app.models.property import Property  # noqa: E402
from app.models.recurring_invoice import RecurringInvoice  # noqa: E402
from app.models.resident_credential import ResidentCredential  # noqa: E402
from app.models.unit import Unit  # noqa: E402

SEED_NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000000")

# Not a real filename - the agreement PDF is now generated on demand from
# the lease's own data (see app/services/lease_agreement_pdf.py). This
# value is just a marker meaning "an agreement is available for this lease".
AGREEMENT_AVAILABLE = "generated"

# App-wide Login feature - real email/password auth for both personas (see
# routers/auth.py). Not secrets worth protecting beyond local dev; printed
# at the end of a seed run.
STAFF_EMAIL = "staff@meridian-residences.example"
STAFF_PASSWORD = "Staff@123"
RESIDENT_PASSWORD = "Resident@123"

LEASES = [
    {
        "label": "LEASE-001",
        "guest_label": "GUEST-001",
        "start_date": date(2026, 1, 1),
        "end_date": date(2026, 12, 31),
        "monthly_rate": Decimal("45000.00"),
        "renewal_date": date(2026, 12, 1),
        "status": "active",
        "agreement_file_url": AGREEMENT_AVAILABLE,
    },
    {
        "label": "LEASE-002",
        "guest_label": "GUEST-002",
        "start_date": date(2027, 1, 1),
        "end_date": date(2027, 12, 31),
        "monthly_rate": Decimal("47000.00"),
        "renewal_date": None,
        "status": "pending",
        "agreement_file_url": None,
    },
    {
        "label": "LEASE-003",
        "guest_label": "GUEST-001",
        "start_date": date(2025, 1, 1),
        "end_date": date(2025, 12, 31),
        "monthly_rate": Decimal("43000.00"),
        "renewal_date": None,
        "status": "expired",
        "agreement_file_url": AGREEMENT_AVAILABLE,
    },
    {
        "label": "LEASE-004",
        "guest_label": "GUEST-002",
        "start_date": date(2024, 6, 1),
        "end_date": date(2025, 5, 31),
        "monthly_rate": Decimal("42000.00"),
        "renewal_date": None,
        "status": "terminated",
        "agreement_file_url": AGREEMENT_AVAILABLE,
    },
]


def seed_id(label: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, label)


def _ensure(db, model, record_id, factory):
    """Insert `factory()` only if `model` with `record_id` doesn't exist yet."""
    if db.get(model, record_id) is None:
        db.add(factory())
        db.flush()
        return True
    return False


def run():
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    guest_ids = {label: seed_id(label) for label in ("GUEST-001", "GUEST-002", "GUEST-003")}
    staff_guest_id = seed_id("STAFF-001")
    property_id = seed_id("PROP-001")
    unit_id = seed_id("UNIT-101")
    property2_id = seed_id("PROP-002")
    unit2_id = seed_id("UNIT-201")

    _ensure(
        db, Guest, guest_ids["GUEST-001"],
        lambda: Guest(id=guest_ids["GUEST-001"], name="Demo Resident", email="demo.resident@example.com", created_at=now),
    )
    _ensure(
        db, Guest, guest_ids["GUEST-002"],
        lambda: Guest(id=guest_ids["GUEST-002"], name="Other Resident", email="other.resident@example.com", created_at=now),
    )
    _ensure(
        db, Guest, guest_ids["GUEST-003"],
        lambda: Guest(id=guest_ids["GUEST-003"], name="Third Resident", email="third.resident@example.com", created_at=now),
    )
    _ensure(
        db, Guest, staff_guest_id,
        lambda: Guest(id=staff_guest_id, name="Property Staff", email=STAFF_EMAIL, created_at=now),
    )

    _ensure(
        db, Property, property_id,
        lambda: Property(id=property_id, name="Meridian Residences", address="Premium Residential Community", brand="Meridian"),
    )
    _ensure(
        db, Property, property2_id,
        lambda: Property(id=property2_id, name="Lakeside Residences", address="Lakeside Residential Community", brand="Lakeside"),
    )

    _ensure(
        db, Unit, unit_id,
        lambda: Unit(id=unit_id, property_id=property_id, unit_number="101", unit_type="2BHK", status="occupied", created_at=now),
    )
    _ensure(
        db, Unit, unit2_id,
        lambda: Unit(id=unit2_id, property_id=property2_id, unit_number="201", unit_type="1BHK", status="occupied", created_at=now),
    )

    # Staff Lease Management feature - real login credential (role="staff",
    # global access - see require_staff in core/security.py). unit_id is a
    # required FK per the ResidentCredential shape ported from
    # feature-lavanya's branch but isn't used to scope staff access.
    _ensure(
        db, ResidentCredential, seed_id("STAFF-CREDENTIAL-001"),
        lambda: ResidentCredential(
            id=seed_id("STAFF-CREDENTIAL-001"),
            guest_id=staff_guest_id,
            unit_id=unit_id,
            email=STAFF_EMAIL,
            password_hash=hash_password(STAFF_PASSWORD),
            role="staff",
            created_at=now,
        ),
    )

    # App-wide Login feature - real login for the resident persona too (same
    # /auth/login endpoint as staff, role="resident").
    resident_credentials = [
        ("GUEST-001", guest_ids["GUEST-001"], unit_id),
        ("GUEST-002", guest_ids["GUEST-002"], unit_id),
        ("GUEST-003", guest_ids["GUEST-003"], unit2_id),
    ]
    for label, resident_guest_id, resident_unit_id in resident_credentials:
        credential_id = seed_id(f"{label}-CREDENTIAL")
        guest = db.get(Guest, resident_guest_id)
        _ensure(
            db, ResidentCredential, credential_id,
            lambda credential_id=credential_id, resident_guest_id=resident_guest_id,
            resident_unit_id=resident_unit_id, guest=guest: ResidentCredential(
                id=credential_id,
                guest_id=resident_guest_id,
                unit_id=resident_unit_id,
                email=guest.email,
                password_hash=hash_password(RESIDENT_PASSWORD),
                role="resident",
                created_at=now,
            ),
        )

    # Maintenance feature (ported from feature-lavanya) - a couple of
    # realistic tickets for GUEST-001/UNIT-101 so the Maintenance page and
    # the Dashboard's Open Requests card have real data immediately.
    _ensure(
        db, MaintenanceTicket, seed_id("TICKET-001"),
        lambda: MaintenanceTicket(
            id=seed_id("TICKET-001"),
            unit_id=unit_id,
            guest_id=guest_ids["GUEST-001"],
            issue_type="plumbing",
            description="Kitchen sink is leaking",
            priority="high",
            status="open",
            vendor_queue=None,
            escalated=False,
            created_at=now,
            updated_at=now,
        ),
    )
    _ensure(
        db, MaintenanceTicket, seed_id("TICKET-002"),
        lambda: MaintenanceTicket(
            id=seed_id("TICKET-002"),
            unit_id=unit_id,
            guest_id=guest_ids["GUEST-001"],
            issue_type="electrical",
            description="Living room outlet not working",
            priority="medium",
            status="resolved",
            vendor_queue="electrical-standard",
            escalated=False,
            created_at=now,
            updated_at=now,
            resolved_at=now,
        ),
    )

    _ensure(
        db, LeaseAgreement, seed_id("LEASE-005"),
        lambda: LeaseAgreement(
            id=seed_id("LEASE-005"),
            unit_id=unit2_id,
            guest_id=guest_ids["GUEST-003"],
            start_date=date(2026, 3, 1),
            end_date=date(2027, 2, 28),
            monthly_rate=Decimal("38000.00"),
            renewal_date=None,
            status="active",
            agreement_file_url=AGREEMENT_AVAILABLE,
            created_at=now,
            updated_at=now,
        ),
    )

    created = []
    for lease in LEASES:
        lease_id = seed_id(lease["label"])
        was_created = _ensure(
            db,
            LeaseAgreement,
            lease_id,
            lambda lease=lease, lease_id=lease_id: LeaseAgreement(
                id=lease_id,
                unit_id=unit_id,
                guest_id=guest_ids[lease["guest_label"]],
                start_date=lease["start_date"],
                end_date=lease["end_date"],
                monthly_rate=lease["monthly_rate"],
                renewal_date=lease["renewal_date"],
                status=lease["status"],
                agreement_file_url=lease["agreement_file_url"],
                created_at=now,
                updated_at=now,
            ),
        )
        if was_created:
            created.append((lease["label"], lease_id))

    # Invoices workflow (ported from feature-annapoorna) - matches that
    # branch's own seed fixture shape (2 paid + 1 overdue) for LEASE-001,
    # re-keyed to our uuid5 id scheme instead of her literal UUIDs so it
    # fits this project's seeding convention.
    lease_001_id = seed_id("LEASE-001")
    INVOICES = [
        {
            "label": "INVOICE-2026-06",
            "billing_period_start": date(2026, 6, 1),
            "billing_period_end": date(2026, 6, 30),
            "due_date": date(2026, 7, 10),
            "payment_status": "paid",
            "generated_at": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "paid_at": datetime(2026, 7, 5, tzinfo=timezone.utc),
        },
        {
            "label": "INVOICE-2026-07",
            "billing_period_start": date(2026, 7, 1),
            "billing_period_end": date(2026, 7, 31),
            "due_date": date(2026, 8, 10),
            "payment_status": "paid",
            "generated_at": datetime(2026, 7, 1, tzinfo=timezone.utc),
            "paid_at": datetime(2026, 8, 5, tzinfo=timezone.utc),
        },
        {
            "label": "INVOICE-2026-08",
            "billing_period_start": date(2026, 8, 1),
            "billing_period_end": date(2026, 8, 31),
            "due_date": date(2026, 9, 10),
            "payment_status": "overdue",
            "generated_at": datetime(2026, 8, 1, tzinfo=timezone.utc),
            "paid_at": None,
        },
    ]
    for invoice in INVOICES:
        invoice_id = seed_id(invoice["label"])
        _ensure(
            db, RecurringInvoice, invoice_id,
            lambda invoice=invoice, invoice_id=invoice_id: RecurringInvoice(
                id=invoice_id,
                lease_id=lease_001_id,
                billing_period_start=invoice["billing_period_start"],
                billing_period_end=invoice["billing_period_end"],
                amount=Decimal("45000.00"),
                due_date=invoice["due_date"],
                payment_status=invoice["payment_status"],
                generated_at=invoice["generated_at"],
                paid_at=invoice["paid_at"],
                created_at=invoice["generated_at"],
                updated_at=invoice["generated_at"],
            ),
        )

    db.commit()

    if not created:
        print("All seed leases already present - nothing to do.")
    for label, lease_id in created:
        print(f"Seeded {label} = {lease_id}")
    print(f"GUEST-001 (primary resident) = {guest_ids['GUEST-001']}")
    print(f"GUEST-002 (other resident) = {guest_ids['GUEST-002']}")
    print(f"GUEST-003 (Lakeside resident) = {guest_ids['GUEST-003']}")
    print(f"Staff login: email={STAFF_EMAIL} password={STAFF_PASSWORD}")
    print(f"Resident login (any of the 3 guests' email above) password={RESIDENT_PASSWORD}")
    print("e.g. demo.resident@example.com / Resident@123")


if __name__ == "__main__":
    run()
