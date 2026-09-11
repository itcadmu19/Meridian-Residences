from app.ai.maintenance_triage_agent import triage_description


def test_water_leak_is_urgent_and_escalated():
    result = triage_description("Kitchen sink is leaking, water leak everywhere", fallback_issue_type="plumbing")
    assert result.priority == "urgent"
    assert result.escalated is True
    assert result.issue_type == "plumbing"
    assert result.vendor_queue == "plumbing-emergency"


def test_no_heat_is_urgent_and_escalated():
    result = triage_description("There is no heat in the apartment", fallback_issue_type="hvac")
    assert result.priority == "urgent"
    assert result.escalated is True
    assert result.issue_type == "hvac"


def test_normal_electrical_request_gets_medium_priority_and_correct_queue():
    result = triage_description("The outlet in the living room is not working", fallback_issue_type="electrical")
    assert result.issue_type == "electrical"
    assert result.priority == "medium"
    assert result.escalated is False
    assert result.vendor_queue == "electrical-standard"


def test_unknown_description_falls_back_to_resident_issue_type():
    result = triage_description("Something feels off in my apartment", fallback_issue_type="appliance")
    assert result.issue_type == "appliance"
    assert result.priority == "medium"
    assert result.escalated is False


def test_result_never_recommends_unsupported_priority_or_issue_type():
    result = triage_description("gas smell near the stove", fallback_issue_type="general")
    assert result.issue_type in ("plumbing", "electrical", "hvac", "appliance", "general", "other")
    assert result.priority in ("low", "medium", "high", "urgent")
