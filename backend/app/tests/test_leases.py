"""
Tests for User Story 1 - View Lease Details.

Covers the frozen minimum (Project Design Document section 23: "get active
lease; unauthorized lease blocked; missing lease returns 404") plus the
gaps identified in the plan (IDOR, invalid UUID, degraded dashboard summary
when Members 2/3's services don't exist yet). Runs against an in-memory
SQLite database via the GUID cross-dialect type - no live Postgres needed.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.guest import Guest
from app.models.lease_agreement import LeaseAgreement
from app.models.property import Property
from app.models.unit import Unit

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_lease(db_session):
    now = datetime.now(timezone.utc)
    guest = Guest(id=uuid.uuid4(), name="Demo Resident", email="demo@example.com", created_at=now)
    other_guest = Guest(id=uuid.uuid4(), name="Other Resident", email="other@example.com", created_at=now)
    prop = Property(id=uuid.uuid4(), name="Meridian Residences", address="123 Main St")
    unit = Unit(
        id=uuid.uuid4(),
        property_id=prop.id,
        unit_number="101",
        unit_type="2BHK",
        status="occupied",
        created_at=now,
    )
    lease = LeaseAgreement(
        id=uuid.uuid4(),
        unit_id=unit.id,
        guest_id=guest.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        monthly_rate=Decimal("45000.00"),
        renewal_date=date(2026, 12, 1),
        status="active",
        created_at=now,
        updated_at=now,
    )
    db_session.add_all([guest, other_guest, prop, unit, lease])
    db_session.commit()
    return {"guest": guest, "other_guest": other_guest, "unit": unit, "lease": lease}


def auth_header(guest_id: uuid.UUID) -> dict:
    token = create_access_token(guest_id)
    return {"Authorization": f"Bearer {token}"}


def test_get_active_lease_returns_200(client, seeded_lease):
    lease = seeded_lease["lease"]
    resp = client.get(f"/api/v1/leases/{lease.id}", headers=auth_header(seeded_lease["guest"].id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "active"
    assert body["data"]["unit"]["unit_number"] == "101"


def test_get_missing_lease_returns_404(client, seeded_lease):
    resp = client.get(
        f"/api/v1/leases/{uuid.uuid4()}", headers=auth_header(seeded_lease["guest"].id)
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "LEASE_NOT_FOUND"


def test_resident_cannot_access_another_residents_lease(client, seeded_lease):
    lease = seeded_lease["lease"]
    resp = client.get(
        f"/api/v1/leases/{lease.id}", headers=auth_header(seeded_lease["other_guest"].id)
    )
    # Uniform 404, not 403 - see plan Decision 5 (avoids confirming the lease exists).
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "LEASE_NOT_FOUND"


def test_unauthenticated_request_returns_401(client, seeded_lease):
    lease = seeded_lease["lease"]
    resp = client.get(f"/api/v1/leases/{lease.id}")
    assert resp.status_code == 401


def test_invalid_uuid_returns_422(client, seeded_lease):
    resp = client.get(
        "/api/v1/leases/not-a-uuid", headers=auth_header(seeded_lease["guest"].id)
    )
    assert resp.status_code == 422


def test_get_guest_leases_returns_own_leases(client, seeded_lease):
    guest = seeded_lease["guest"]
    resp = client.get(f"/api/v1/guests/{guest.id}/leases", headers=auth_header(guest.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total"] == 1
    assert len(body["data"]) == 1


def test_dashboard_summary_degrades_gracefully_without_invoice_or_maintenance_services(
    client, seeded_lease
):
    lease = seeded_lease["lease"]
    resp = client.get(
        f"/api/v1/leases/{lease.id}/summary", headers=auth_header(seeded_lease["guest"].id)
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Members 2/3's services don't exist yet in this repo - must degrade, not error.
    assert data["next_payment"] is None
    assert data["open_requests"] == 0
    assert data["lease_status"] == "active"
    # The lease's own creation still produces one activity entry.
    assert len(data["activities"]) == 1
    assert data["activities"][0]["type"] == "lease"
