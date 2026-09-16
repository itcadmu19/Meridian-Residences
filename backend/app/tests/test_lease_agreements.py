"""
Tests for the AI-Generated Lease Agreement workflow - self-contained per
this codebase's per-file test convention (own in-memory SQLite engine, own
fixtures, own auth_header() helper - see test_leases.py).
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
    prop = Property(id=uuid.uuid4(), name="Meridian Residences", brand="Meridian", address="123 Main St")
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
    return {"guest": guest, "other_guest": other_guest, "lease": lease}


def auth_header(guest_id: uuid.UUID, role: str = "resident") -> dict:
    token = create_access_token(guest_id, role=role)
    return {"Authorization": f"Bearer {token}"}


STAFF_ID = uuid.uuid4()
GENERATE_PAYLOAD = {"security_deposit": "90000.00"}


def test_staff_generate_requires_security_deposit(client, seeded_lease):
    lease_id = seeded_lease["lease"].id
    resp = client.post(
        f"/api/v1/leases/{lease_id}/generate-agreement",
        json={},
        headers=auth_header(STAFF_ID, role="staff"),
    )
    assert resp.status_code == 422, resp.text


def test_staff_generate_creates_draft_v1(client, seeded_lease):
    lease_id = seeded_lease["lease"].id
    resp = client.post(
        f"/api/v1/leases/{lease_id}/generate-agreement",
        json=GENERATE_PAYLOAD,
        headers=auth_header(STAFF_ID, role="staff"),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()["data"]
    assert body["status"] == "draft"
    assert body["version"] == 1
    assert "AI-GENERATED DRAFT" in body["content"]
    assert "Demo Resident" in body["content"]


def test_resident_cannot_generate(client, seeded_lease):
    lease_id = seeded_lease["lease"].id
    resp = client.post(
        f"/api/v1/leases/{lease_id}/generate-agreement",
        json=GENERATE_PAYLOAD,
        headers=auth_header(seeded_lease["guest"].id),
    )
    assert resp.status_code == 403, resp.text


def test_resident_cannot_see_draft(client, seeded_lease):
    lease_id = seeded_lease["lease"].id
    client.post(
        f"/api/v1/leases/{lease_id}/generate-agreement",
        json=GENERATE_PAYLOAD,
        headers=auth_header(STAFF_ID, role="staff"),
    )
    resp = client.get(f"/api/v1/leases/{lease_id}/agreement-document", headers=auth_header(seeded_lease["guest"].id))
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] is None


def test_full_generate_edit_send_accept_flow(client, seeded_lease):
    lease_id = seeded_lease["lease"].id
    guest_id = seeded_lease["guest"].id
    staff_headers = auth_header(STAFF_ID, role="staff")
    resident_headers = auth_header(guest_id)

    generate_resp = client.post(f"/api/v1/leases/{lease_id}/generate-agreement", json=GENERATE_PAYLOAD, headers=staff_headers)
    assert generate_resp.status_code == 201

    edit_resp = client.put(
        f"/api/v1/leases/{lease_id}/agreement-document",
        json={"content": "Edited draft content by staff."},
        headers=staff_headers,
    )
    assert edit_resp.status_code == 200, edit_resp.text
    assert edit_resp.json()["data"]["content"] == "Edited draft content by staff."

    send_resp = client.post(f"/api/v1/leases/{lease_id}/agreement-document/send", headers=staff_headers)
    assert send_resp.status_code == 200
    assert send_resp.json()["data"]["status"] == "sent_to_resident"

    resident_view = client.get(f"/api/v1/leases/{lease_id}/agreement-document", headers=resident_headers)
    assert resident_view.status_code == 200
    assert resident_view.json()["data"]["status"] == "sent_to_resident"

    accept_resp = client.post(f"/api/v1/leases/{lease_id}/agreement-document/accept", headers=resident_headers)
    assert accept_resp.status_code == 200, accept_resp.text
    accepted = accept_resp.json()["data"]
    assert accepted["status"] == "accepted"
    assert accepted["accepted_at"] is not None

    # Second accept attempt on the already-accepted version -> conflict.
    second_accept = client.post(f"/api/v1/leases/{lease_id}/agreement-document/accept", headers=resident_headers)
    assert second_accept.status_code == 409, second_accept.text

    # Persists after a fresh request (proves it's not frontend-only state).
    refetch = client.get(f"/api/v1/leases/{lease_id}/agreement-document", headers=resident_headers)
    assert refetch.json()["data"]["status"] == "accepted"


def test_enquiry_and_staff_response_flow(client, seeded_lease):
    lease_id = seeded_lease["lease"].id
    guest_id = seeded_lease["guest"].id
    staff_headers = auth_header(STAFF_ID, role="staff")
    resident_headers = auth_header(guest_id)

    client.post(f"/api/v1/leases/{lease_id}/generate-agreement", json=GENERATE_PAYLOAD, headers=staff_headers)
    client.post(f"/api/v1/leases/{lease_id}/agreement-document/send", headers=staff_headers)

    enquiry_resp = client.post(
        f"/api/v1/leases/{lease_id}/enquiries",
        json={"subject": "Security Deposit", "message": "Can you explain the deposit refund process?", "reference": "Clause 5"},
        headers=resident_headers,
    )
    assert enquiry_resp.status_code == 201, enquiry_resp.text
    enquiry = enquiry_resp.json()["data"]
    assert enquiry["status"] == "open"

    list_resp = client.get(f"/api/v1/leases/{lease_id}/enquiries", headers=staff_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) == 1

    respond_resp = client.post(
        f"/api/v1/leases/{lease_id}/enquiries/{enquiry['id']}/respond",
        json={"response": "The deposit is refunded within 30 days of move-out, minus deductions."},
        headers=staff_headers,
    )
    assert respond_resp.status_code == 200, respond_resp.text
    assert respond_resp.json()["data"]["status"] == "answered"

    # Resident cannot respond to their own enquiry (staff-only action).
    forbidden = client.post(
        f"/api/v1/leases/{lease_id}/enquiries/{enquiry['id']}/respond",
        json={"response": "trying as resident"},
        headers=resident_headers,
    )
    assert forbidden.status_code == 403


def test_regenerate_supersedes_previous_version(client, seeded_lease):
    lease_id = seeded_lease["lease"].id
    guest_id = seeded_lease["guest"].id
    staff_headers = auth_header(STAFF_ID, role="staff")
    resident_headers = auth_header(guest_id)

    client.post(f"/api/v1/leases/{lease_id}/generate-agreement", json=GENERATE_PAYLOAD, headers=staff_headers)
    client.post(f"/api/v1/leases/{lease_id}/agreement-document/send", headers=staff_headers)

    regenerate_resp = client.post(f"/api/v1/leases/{lease_id}/generate-agreement", json=GENERATE_PAYLOAD, headers=staff_headers)
    assert regenerate_resp.status_code == 201
    assert regenerate_resp.json()["data"]["version"] == 2
    assert regenerate_resp.json()["data"]["status"] == "draft"

    # Resident still can't see the new draft until it's sent again.
    resident_view = client.get(f"/api/v1/leases/{lease_id}/agreement-document", headers=resident_headers)
    assert resident_view.json()["data"] is None

    # Nothing to accept yet - v2 hasn't been sent.
    accept_resp = client.post(f"/api/v1/leases/{lease_id}/agreement-document/accept", headers=resident_headers)
    assert accept_resp.status_code == 409


def test_security_resident_a_cannot_access_resident_b_lease(client, seeded_lease):
    lease_id = seeded_lease["lease"].id
    other_guest_id = seeded_lease["other_guest"].id
    staff_headers = auth_header(STAFF_ID, role="staff")

    client.post(f"/api/v1/leases/{lease_id}/generate-agreement", json=GENERATE_PAYLOAD, headers=staff_headers)
    client.post(f"/api/v1/leases/{lease_id}/agreement-document/send", headers=staff_headers)

    other_headers = auth_header(other_guest_id)
    get_resp = client.get(f"/api/v1/leases/{lease_id}/agreement-document", headers=other_headers)
    assert get_resp.status_code == 404

    accept_resp = client.post(f"/api/v1/leases/{lease_id}/agreement-document/accept", headers=other_headers)
    assert accept_resp.status_code == 404

    enquiry_resp = client.post(
        f"/api/v1/leases/{lease_id}/enquiries",
        json={"subject": "x", "message": "y"},
        headers=other_headers,
    )
    assert enquiry_resp.status_code == 404


def test_staff_action_on_nonexistent_lease_returns_404(client, seeded_lease):
    fake_lease_id = uuid.uuid4()
    staff_headers = auth_header(STAFF_ID, role="staff")

    resp = client.post(f"/api/v1/leases/{fake_lease_id}/generate-agreement", json=GENERATE_PAYLOAD, headers=staff_headers)
    assert resp.status_code == 404

    resp = client.post(f"/api/v1/leases/{fake_lease_id}/agreement-document/send", headers=staff_headers)
    assert resp.status_code == 404


def test_unauthenticated_requests_fail(client, seeded_lease):
    lease_id = seeded_lease["lease"].id

    assert client.get(f"/api/v1/leases/{lease_id}/agreement-document").status_code == 401
    assert client.post(f"/api/v1/leases/{lease_id}/agreement-document/accept").status_code == 401
    assert client.post(f"/api/v1/leases/{lease_id}/generate-agreement", json=GENERATE_PAYLOAD).status_code == 401
    assert client.get(f"/api/v1/leases/{lease_id}/enquiries").status_code == 401
