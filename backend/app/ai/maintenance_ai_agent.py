"""Optional real-AI triage for maintenance tickets - ported from a newer
copy of teammate feature-lavanya's branch, rewritten to reuse this app's
own `ai/ollama_client.py` (already fixed to fail fast when Ollama isn't
running - see that module's docstring) instead of duplicating raw
`urllib` calls against a hardcoded `http://ollama:11434` docker-compose
service hostname, which would never resolve outside a compose network and
carries the same slow-timeout risk `ollama_client.py` was fixed for.

Best-effort, same shape as `ai/invoice_insight_agent.py`: if Ollama is
unavailable, times out, or returns malformed data, callers get the
existing deterministic rule-based result - triage never hard-fails.
"""

import logging

from app.ai import ollama_client
from app.ai.maintenance_triage_agent import ISSUE_TYPES, PRIORITIES, TriageResult, triage_description

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a maintenance triage assistant for a residential property "
    "management app. Classify the maintenance request described by the "
    "resident. Respond with ONLY a JSON object with exactly these keys: "
    f'"issue_type" (one of {ISSUE_TYPES}), "priority" (one of {PRIORITIES}), '
    '"escalated" (true only for an immediate safety or serious property '
    'risk), and "reason" (one short sentence explaining the classification). '
    "Never invent details that were not in the request."
)


def triage_with_ai(description: str, fallback_issue_type: str = "general") -> TriageResult:
    """Uses the local Ollama model configured in core/config.py, falling
    back to the deterministic rule-based `triage_description` on any
    failure (Ollama not running, malformed response, etc.)."""
    rule_result = triage_description(description, fallback_issue_type=fallback_issue_type)

    try:
        result = ollama_client.generate_json(description, system=_SYSTEM_PROMPT)
        issue_type = result["issue_type"]
        priority = result["priority"]
        escalated = result["escalated"]
        reason = result["reason"]
        if issue_type not in ISSUE_TYPES or priority not in PRIORITIES:
            raise ValueError(f"AI returned an unsupported classification: {result!r}")
        if not isinstance(escalated, bool) or not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"AI returned an invalid triage result: {result!r}")
        return TriageResult(
            issue_type=issue_type,
            priority=priority,
            vendor_queue=f"{issue_type}-{'emergency' if escalated else 'standard'}",
            escalated=escalated,
            reason=reason.strip(),
        )
    except Exception as exc:  # noqa: BLE001 - any LLM/network failure falls back safely
        logger.warning("Falling back to rule-based maintenance triage: %s", exc)
        return rule_result
