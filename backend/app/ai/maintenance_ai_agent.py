"""Optional AI triage for Member 3 maintenance tickets.

The provider is deliberately best-effort. If it is not configured, times out,
returns malformed data, or raises any provider error, callers receive the
existing deterministic rule-based result.
"""

import json
import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.ai.maintenance_triage_agent import ISSUE_TYPES, PRIORITIES, TriageResult, triage_description

logger = logging.getLogger(__name__)


def triage_with_ai(
    description: str,
    fallback_issue_type: str = "general",
    *,
    api_url: str = "http://ollama:11434/api/generate",
    api_key: str | None = None,
    model: str = "llama3.2",
    timeout_seconds: float = 30.0,
) -> TriageResult:
    """Use a local Ollama model, falling back to local rules."""
    rule_result = triage_description(description, fallback_issue_type=fallback_issue_type)
    if not api_url:
        return rule_result

    prompt = (
        "Classify this maintenance request. Return only JSON with exactly these "
        "keys: issue_type, priority, escalated, reason. "
        f"issue_type must be one of {ISSUE_TYPES}; priority must be one of {PRIORITIES}; "
        "escalated must be true only for an immediate safety or serious property risk.\n\n"
        f"Request: {description}"
    )
    payload = {"model": model, "prompt": prompt, "format": "json", "stream": False, "options": {"temperature": 0}}

    try:
        request = Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=timeout_seconds) as response:
            provider_response = json.loads(response.read().decode("utf-8"))
        content = provider_response["response"]
        result = json.loads(content) if isinstance(content, str) else content
        issue_type = result["issue_type"]
        priority = result["priority"]
        escalated = result["escalated"]
        reason = result["reason"]
        if issue_type not in ISSUE_TYPES or priority not in PRIORITIES:
            raise ValueError("AI returned an unsupported classification")
        if not isinstance(escalated, bool) or not isinstance(reason, str) or not reason.strip():
            raise ValueError("AI returned an invalid triage result")
        return TriageResult(
            issue_type=issue_type,
            priority=priority,
            vendor_queue=f"{issue_type}-{'emergency' if escalated else 'standard'}",
            escalated=escalated,
            reason=reason.strip(),
        )
    except (KeyError, TypeError, ValueError, IndexError, json.JSONDecodeError, URLError, TimeoutError, OSError) as exc:
        logger.warning("AI maintenance triage failed; using rule-based fallback: %s", exc)
        return rule_result