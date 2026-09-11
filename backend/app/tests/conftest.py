import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import engine, get_db
from app.core.security import hash_password
from app.main import app
from app.models.guest import Guest
from app.models.property import Property
from app.models.resident_credential import ResidentCredential
from app.models.unit import Unit

DEMO_PASSWORD = "TestPass123!"



@pytest.fixture()
def db_session():
    """Each test runs inside a transaction that is rolled back afterward."""
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session: Session = TestSession()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def guest_and_unit(db_session):
    guest = Guest(id=uuid.uuid4(), name="Test Resident", email=f"{uuid.uuid4()}@example.com")
    property_ = Property(id=uuid.uuid4(), name="Test Property", timezone="UTC")
    db_session.add_all([guest, property_])
    db_session.flush()

    unit = Unit(id=uuid.uuid4(), property_id=property_.id, unit_number="101", status="occupied")
    db_session.add(unit)
    db_session.commit()

    return guest, unit


@pytest.fixture()
def resident_credential(db_session, guest_and_unit):
    guest, unit = guest_and_unit
    email = f"{uuid.uuid4()}@example.com"
    credential = ResidentCredential(
        id=uuid.uuid4(),
        guest_id=guest.id,
        unit_id=unit.id,
        email=email,
        password_hash=hash_password(DEMO_PASSWORD),
        role="resident",
    )
    db_session.add(credential)
    db_session.commit()
    return credential, email, DEMO_PASSWORD


@pytest.fixture()
def auth_headers(client, resident_credential):
    _, email, password = resident_credential
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
