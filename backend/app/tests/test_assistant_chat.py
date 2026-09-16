"""
Tests for the AI Assistant chat endpoint - ported from teammate
feature-Sanjana's branch, adapted to this app's per-file, self-contained
test fixture convention (see test_leases.py: its own in-memory SQLite
engine/session/client, no shared conftest.py) and to require resident
authentication, which her branch's tests never exercised (her router had
none).

Chunks are seeded directly in the test DB instead of relying on
file-based seeding, so these tests don't depend on the real documents/
directory contents.
"""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.document import Document, DocumentChunk

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session(monkeypatch):
    Base.metadata.create_all(bind=engine)
    # assistant_service opens its own SessionLocal() internally (retrieval
    # runs outside the request's injected db session) - point that at the
    # same in-memory engine used by the test client.
    monkeypatch.setattr("app.services.assistant_service.SessionLocal", TestingSessionLocal)
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
def seeded_documents(db_session):
    now = datetime.now(timezone.utc)
    parking_doc = Document(
        id=uuid.uuid4(),
        title="Parking Policy",
        document_type="building_policy",
        source_path="parking_policy.txt",
        version="1.0",
        created_at=now,
    )
    lease_doc = Document(
        id=uuid.uuid4(),
        title="Early Termination",
        document_type="lease_terms",
        source_path="early_termination.txt",
        version="1.0",
        created_at=now,
    )
    db_session.add_all([parking_doc, lease_doc])
    db_session.flush()

    db_session.add_all(
        [
            DocumentChunk(
                id=uuid.uuid4(),
                document_id=parking_doc.id,
                chunk_index=0,
                content=(
                    "Parking is included for one vehicle per apartment. Residents may park "
                    "one standard passenger vehicle in the assigned space at no additional charge."
                ),
                created_at=now,
            ),
            DocumentChunk(
                id=uuid.uuid4(),
                document_id=lease_doc.id,
                chunk_index=0,
                content=(
                    "A resident who chooses to terminate the lease early must provide 60 days "
                    "written notice to the management office."
                ),
                created_at=now,
            ),
        ]
    )
    db_session.commit()
    return {"parking_doc": parking_doc, "lease_doc": lease_doc}


def resident_auth_header() -> dict:
    token = create_access_token(uuid.uuid4(), role="resident")
    return {"Authorization": f"Bearer {token}"}


def staff_auth_header() -> dict:
    token = create_access_token(uuid.uuid4(), role="staff")
    return {"Authorization": f"Bearer {token}"}


def test_supported_question_returns_grounded_answer_with_sources(client, seeded_documents):
    resp = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Is parking included?"},
        headers=resident_auth_header(),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["conversation_id"]
    assert "parking" in body["data"]["answer"].lower()
    assert len(body["data"]["sources"]) >= 1


def test_unsupported_question_returns_clear_no_sources_response(client, seeded_documents):
    resp = client.post(
        "/api/v1/assistant/chat",
        json={"message": "What are the restaurant hours?"},
        headers=resident_auth_header(),
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["sources"] == []
    assert "cannot find this in the lease or building policy documents" in body["data"]["answer"].lower()


def test_empty_question_returns_422_validation_error(client, seeded_documents):
    resp = client.post(
        "/api/v1/assistant/chat",
        json={"message": ""},
        headers=resident_auth_header(),
    )

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["success"] is False
    assert body["error_code"] == "VALIDATION_ERROR"


def test_conversation_id_is_preserved_across_calls(client, seeded_documents):
    conversation_id = "f3af9e8a-0f0a-4614-a7df-9a53d5c9d01d"
    headers = resident_auth_header()

    first = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Does parking cost extra?", "conversation_id": conversation_id},
        headers=headers,
    )
    second = client.post(
        "/api/v1/assistant/chat",
        json={"message": "What is the early termination notice?", "conversation_id": conversation_id},
        headers=headers,
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["data"]["conversation_id"] == conversation_id
    assert second.json()["data"]["conversation_id"] == conversation_id


def test_staff_cannot_access_assistant(client, seeded_documents):
    resp = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Is parking included?"},
        headers=staff_auth_header(),
    )
    assert resp.status_code == 403, resp.text


def test_unauthenticated_request_returns_401(client, seeded_documents):
    resp = client.post("/api/v1/assistant/chat", json={"message": "Is parking included?"})
    assert resp.status_code == 401, resp.text
