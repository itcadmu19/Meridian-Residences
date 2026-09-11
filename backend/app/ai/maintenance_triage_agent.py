"""Member 3 — Maintenance AI triage agent (Design Contract §20).

Stopping condition: classify the ticket, choose a vendor queue, set escalation
when required, then return the result once. This module never loops or retries
on its own — the caller (service layer) applies the result and stops.
"""

from dataclasses import dataclass

ISSUE_TYPES = ("plumbing", "electrical", "hvac", "appliance", "general", "other")
PRIORITIES = ("low", "medium", "high", "urgent")

# Ordered rules: first matching rule wins. Urgent/safety issues are listed first
# so a description mentioning both a minor and a dangerous symptom escalates.
_RULES = (
    # (keywords, issue_type, priority, escalate, reason)
    (("water leak", "leaking", "flooding", "flooded", "burst pipe"), "plumbing", "urgent", True,
     "Water leak requires urgent escalation."),
    (("no heat", "no heating", "furnace not working", "freezing"), "hvac", "urgent", True,
     "No heat requires urgent escalation."),
    (("gas smell", "smell of gas", "gas leak"), "general", "urgent", True,
     "Gas leak risk requires urgent escalation."),
    (("smoke", "fire", "sparking", "sparks"), "electrical", "urgent", True,
     "Fire/electrical safety risk requires urgent escalation."),
    (("no power", "power outage", "no electricity"), "electrical", "urgent", True,
     "Full loss of power requires urgent escalation."),
    (("no hot water",), "plumbing", "high", False,
     "Loss of hot water is a high-priority plumbing issue."),
    (("clogged", "blocked drain", "toilet", "faucet", "pipe", "drain", "plumbing"), "plumbing", "medium", False,
     "Standard plumbing issue."),
    (("outlet", "wiring", "breaker", "electrical", "light fixture", "switch"), "electrical", "medium", False,
     "Standard electrical issue."),
    (("ac ", "air condition", "thermostat", "hvac", "heater"), "hvac", "medium", False,
     "Standard HVAC issue."),
    (("fridge", "refrigerator", "oven", "stove", "dishwasher", "washer", "dryer", "appliance"), "appliance", "medium", False,
     "Standard appliance issue."),
    (("cosmetic", "scratch", "scuff", "squeak", "minor"), "general", "low", False,
     "Minor/cosmetic issue."),
)

_VENDOR_QUEUE_SUFFIX = {True: "emergency", False: "standard"}


@dataclass(frozen=True)
class TriageResult:
    issue_type: str
    priority: str
    vendor_queue: str
    escalated: bool
    reason: str


def triage_description(description: str, fallback_issue_type: str = "general") -> TriageResult:
    """Classify a maintenance ticket description deterministically.

    Falls back to the resident-submitted issue_type at medium priority when no
    rule matches, so every ticket always receives a definite classification.
    """
    text = (description or "").lower()

    for keywords, issue_type, priority, escalate, reason in _RULES:
        if any(keyword in text for keyword in keywords):
            vendor_queue = f"{issue_type}-{_VENDOR_QUEUE_SUFFIX[escalate]}"
            return TriageResult(
                issue_type=issue_type,
                priority=priority,
                vendor_queue=vendor_queue,
                escalated=escalate,
                reason=reason,
            )

    safe_issue_type = fallback_issue_type if fallback_issue_type in ISSUE_TYPES else "general"
    return TriageResult(
        issue_type=safe_issue_type,
        priority="medium",
        vendor_queue=f"{safe_issue_type}-standard",
        escalated=False,
        reason="No urgent keywords detected; routed at standard priority.",
    )
