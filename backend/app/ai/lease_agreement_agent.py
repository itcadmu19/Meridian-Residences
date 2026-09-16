"""
AI-Generated Lease Agreement workflow - draft generator.

Per the feature's legal-safety requirement, this does NOT ask an LLM to
freely draft a contract. Every legally load-bearing clause (parties,
premises, term, rent, deposit, responsibilities, notice, late-payment,
renewal) is rendered by a deterministic Python template directly from the
structured facts passed in - zero hallucination risk, since nothing there
is model-generated. A missing optional fact is rendered as an explicit
`[REQUIRES STAFF REVIEW: ...]` marker rather than invented.

The only AI-generated part is one short framing paragraph at the top,
using the same 2-tier fallback shape as invoice_insight_agent.py (Ollama
-> deterministic). Its output is validated before being trusted: if it
contains any number not present in the supplied facts, it's discarded as
a likely invention and the deterministic fallback sentence is used
instead - the model may choose words, never figures.
"""

from __future__ import annotations

import logging
import re

from app.ai import ollama_client

logger = logging.getLogger(__name__)

DRAFT_BANNER = "AI-GENERATED DRAFT — REVIEW BEFORE SENDING TO THE RESIDENT."

_SYSTEM_PROMPT = (
    "You write a single short introductory paragraph (2-3 sentences) for a "
    "residential lease agreement, in plain, friendly, professional language. "
    "Use ONLY the facts given below. Do not invent or restate any name, date, "
    "amount, or clause not explicitly provided. Do not include any numbers "
    "other than the ones given to you. Output ONLY the paragraph text, no "
    "heading, no markdown."
)


def _missing(value) -> str:
    return "[REQUIRES STAFF REVIEW]" if value in (None, "") else str(value)


def _ordinal(day: int) -> str:
    if 10 <= day % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def _numbers_in(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def _generate_summary_paragraph(context: dict) -> str:
    fallback = (
        f"This lease agreement is between {context['management_name']} and "
        f"{context['resident_name']} for Unit {context['unit_number']} at "
        f"{context['property_name']}, for the term {context['start_date']} to "
        f"{context['end_date']} at a monthly rent of {context['monthly_rate']}."
    )

    facts_lines = "\n".join(f"{key}: {value}" for key, value in context.items())
    known_numbers = _numbers_in(facts_lines)

    try:
        text = ollama_client.generate_text(facts_lines, system=_SYSTEM_PROMPT).strip()
        if not text:
            raise ValueError("Empty response from LLM")
        if not _numbers_in(text) <= known_numbers:
            raise ValueError("Model introduced a number not present in the supplied facts")
        return text
    except Exception as exc:  # noqa: BLE001 - any LLM/network/validation failure falls back safely
        logger.warning("Falling back to deterministic lease summary paragraph: %s", exc)
        return fallback


def _render_template(context: dict) -> str:
    return f"""RESIDENTIAL LEASE AGREEMENT

1. PARTIES
This agreement is made between {context['management_name']} ("Management"),
operating {context['property_name']}, and {context['resident_name']}
("Resident").

2. PREMISES
Management leases to Resident Unit {context['unit_number']}
({_missing(context.get('unit_type'))}) at {context['property_name']},
{_missing(context.get('property_address'))} ("the Premises").

3. TERM
This lease begins on {context['start_date']} and ends on {context['end_date']}.

4. RENT
Resident shall pay monthly rent of {context['monthly_rate']}, due on the
{_ordinal(context['payment_due_day'])} day of each month.

5. SECURITY DEPOSIT
Resident shall pay a security deposit of {context['security_deposit']} prior
to occupancy, refundable per Management's standard move-out inspection
process, less any lawful deductions.

6. MAINTENANCE RESPONSIBILITY
{context['maintenance_responsibility']}

7. UTILITIES RESPONSIBILITY
{context['utilities_responsibility']}

8. OCCUPANCY TERMS
{context['occupancy_terms']}

9. NOTICE PERIOD / EARLY TERMINATION
Resident must provide {context['notice_period_days']} days' written notice
before terminating this lease early or vacating at term end.

10. LATE PAYMENT
{context['late_payment_terms']}

11. RENEWAL
{context['renewal_terms']}

---
This draft was assembled from the structured lease data on file and is
provided for Management's review. It does not constitute legal advice and
is not guaranteed to satisfy all applicable local legal requirements -
Management should review it (and consult counsel if needed) before sending
it to the Resident.
"""


def generate_agreement_draft(context: dict) -> str:
    """`context` must supply every key referenced in `_render_template`
    (callers fill defaults for anything optional before calling this)."""
    summary = _generate_summary_paragraph(context)
    body = _render_template(context)
    return f"{DRAFT_BANNER}\n\n{summary}\n\n{body}"
