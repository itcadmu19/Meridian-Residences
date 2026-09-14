from app.ai.maintenance_ai_agent import triage_with_ai


def test_ai_agent_is_rule_based_when_provider_is_not_configured():
    result = triage_with_ai("Kitchen sink is leaking", fallback_issue_type="plumbing")

    assert result.priority == "urgent"
    assert result.vendor_queue == "plumbing-emergency"


def test_ai_agent_falls_back_when_provider_returns_invalid_json(monkeypatch):
    class InvalidResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"choices": [{"message": {"content": "not json"}}]}'

    monkeypatch.setattr("app.ai.maintenance_ai_agent.urlopen", lambda *args, **kwargs: InvalidResponse())

    result = triage_with_ai(
        "The outlet in the living room is not working",
        fallback_issue_type="electrical",
        api_url="http://ai.test/v1/chat/completions",
        api_key="test-key",
    )

    assert result.issue_type == "electrical"
    assert result.priority == "medium"
    assert result.vendor_queue == "electrical-standard"