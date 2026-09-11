import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_meridian.db")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_supported_question_returns_grounded_answer_with_sources():
    response = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Is parking included?"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["message"] is None
    assert body["data"]["conversation_id"]
    assert body["data"]["answer"]
    assert "parking" in body["data"]["answer"].lower()
    assert len(body["data"]["sources"]) >= 1


def test_unsupported_question_returns_clear_no_sources_response():
    response = client.post(
        "/api/v1/assistant/chat",
        json={"message": "What are the restaurant hours?"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["sources"] == []
    assert "cannot find this in the lease or building policy documents" in body["data"]["answer"].lower()


def test_empty_question_returns_422_validation_error():
    response = client.post(
        "/api/v1/assistant/chat",
        json={"message": ""},
    )

    assert response.status_code == 422, response.text
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Question is required."
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["meta"]["request_id"]


def test_conversation_id_is_preserved_across_calls():
    conversation_id = "f3af9e8a-0f0a-4614-a7df-9a53d5c9d01d"

    first = client.post(
        "/api/v1/assistant/chat",
        json={"message": "Does parking cost extra?", "conversation_id": conversation_id},
    )
    second = client.post(
        "/api/v1/assistant/chat",
        json={"message": "What is the early termination notice?", "conversation_id": conversation_id},
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["data"]["conversation_id"] == conversation_id
    assert second.json()["data"]["conversation_id"] == conversation_id
