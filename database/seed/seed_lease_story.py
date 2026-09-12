"""
Seed data for User Story 1 - View Lease Details.

Uses the logical seed IDs from the Project Design Document section 22
(GUEST-001, PROP-001, UNIT-101, LEASE-001) as deterministic UUIDs (derived
via uuid5) so every developer gets the same IDs locally without needing to
share a database dump. Run from backend/ with the venv active and
DATABASE_URL set, e.g.:

    DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/meridian_residences \
        python ../database/seed/seed_lease_story.py
"""

import sys
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.database import SessionLocal  # noqa: E402
from app.models.guest import Guest  # noqa: E402
from app.models.lease_agreement import LeaseAgreement  # noqa: E402
from app.models.property import Property  # noqa: E402
from app.models.unit import Unit  # noqa: E402

SEED_NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000000")


def seed_id(label: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, label)


def run():
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    guest_id = seed_id("GUEST-001")
    other_guest_id = seed_id("GUEST-002")
    property_id = seed_id("PROP-001")
    unit_id = seed_id("UNIT-101")
    lease_id = seed_id("LEASE-001")

    if db.get(LeaseAgreement, lease_id) is not None:
        print("Seed data already present (LEASE-001 exists) - nothing to do.")
        return

    db.add_all(
        [
            Guest(id=guest_id, name="Demo Resident", email="demo.resident@example.com", created_at=now),
            Guest(id=other_guest_id, name="Other Resident", email="other.resident@example.com", created_at=now),
            Property(id=property_id, name="Meridian Residences", address="Premium Residential Community", brand="Meridian"),
        ]
    )
    db.flush()

    db.add(
        Unit(
            id=unit_id,
            property_id=property_id,
            unit_number="101",
            unit_type="2BHK",
            status="occupied",
            created_at=now,
        )
    )
    db.flush()

    db.add(
        LeaseAgreement(
            id=lease_id,
            unit_id=unit_id,
            guest_id=guest_id,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            monthly_rate=Decimal("45000.00"),
            renewal_date=date(2026, 12, 1),
            status="active",
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()

    print(f"Seeded LEASE-001 = {lease_id}")
    print(f"Seeded GUEST-001 (owner)  = {guest_id}")
    print(f"Seeded GUEST-002 (other)  = {other_guest_id}")


if __name__ == "__main__":
    run()
