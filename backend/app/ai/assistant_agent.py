"""
AI Assistant answer generation - ported from teammate feature-Sanjana's
branch (assistant_service.generate_answer), which only tried OpenAI before
falling back to a deterministic grounded extraction. Rewritten as a 3-tier
fallback that reuses this app's existing local-LLM pattern instead of
requiring a paid API key for the feature to work at all:

    1. Cloud LLM (OpenAI) - only attempted if settings.llm_api_key is set;
       lazy-imported so the `openai` package is an optional dependency.
    2. Local Ollama - via ollama_client.generate_text, same pattern already
       used by invoice_insight_agent.py and maintenance_ai_agent.py.
    3. Deterministic grounded extraction - always available, zero config,
       zero network calls. Also what keeps the test suite deterministic.

Every tier falls through silently on failure, matching the rest of this
app's AI features: the assistant never hard-fails because an LLM is
unavailable.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.ai import ollama_client
from app.core.config import settings

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "a", "an", "the", "is", "are", "am", "do", "does", "did", "can", "could",
    "will", "would", "should", "of", "in", "on", "for", "to", "my", "your",
    "i", "what", "when", "how", "much", "many", "if", "and", "or", "it",
    "this", "that", "before", "give", "need", "happens", "about",
}

_YES_NO_STARTERS = ("is ", "are ", "does ", "do ", "can ", "will ", "should ")
_NEGATION_WORDS = ("not ", "cannot", "no ", "prohibited", "isn't", "aren't", "don't", "doesn't")

NO_ANSWER_MESSAGE = (
    "I cannot find this in the lease or building policy documents. "
    "Please contact the resident office for more detail."
)

_SYSTEM_PROMPT = (
    "You are a resident assistant for Meridian Residences. You must answer "
    "strictly using only the context provided in the user message. If the "
    "context does not answer the question, respond exactly with: "
    f'"{NO_ANSWER_MESSAGE}"'
)


def _build_prompt(question: str, context: str) -> str:
    return (
        "Context:\n"
        f"{context}\n\n"
        f"Question: {question}\n\n"
        "Answer the question using ONLY the context above. Do not use any "
        "outside knowledge or make assumptions beyond what is stated in the "
        f'context. If the context does not answer the question, respond '
        f'exactly with: "{NO_ANSWER_MESSAGE}"'
    )


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.llm_api_key)
    response = client.responses.create(
        model=settings.llm_model or "gpt-4o-mini",
        input=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    answer = response.output_text
    if not answer or not answer.strip():
        raise ValueError("Empty response from LLM")
    return answer.strip()


def _call_ollama(prompt: str) -> str:
    return ollama_client.generate_text(prompt, system=_SYSTEM_PROMPT)


def _split_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]


def _strip_title_prefix(title: str, text: str) -> str:
    """Chunking sometimes merges a document's short title paragraph into
    its first content chunk (e.g. "Parking Policy Parking is included...") -
    drop that leaked title so the answer doesn't start with a duplicate,
    unnatural-sounding heading."""
    if title and text.lower().startswith(title.lower()):
        stripped = text[len(title):].strip()
        if stripped:
            return stripped
    return text


def _question_tokens(question: str) -> set[str]:
    words = re.findall(r"[a-z']+", question.lower())
    return {word for word in words if word not in _STOPWORDS}


def _best_sentence(question: str, text: str) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return text
    if len(sentences) == 1:
        return sentences[0]

    tokens = _question_tokens(question)
    if not tokens:
        return sentences[0]

    def score(sentence: str) -> int:
        sentence_tokens = set(re.findall(r"[a-z']+", sentence.lower()))
        return len(tokens & sentence_tokens)

    return max(sentences, key=score)


def _phrase_naturally(question: str, sentence: str) -> str:
    """Rule-based fallback (no LLM available) - answers a yes/no-shaped
    question with a leading Yes/No instead of just echoing the source
    sentence verbatim, so it reads like an answer rather than a quote."""
    lower_question = question.strip().lower()
    if not lower_question.startswith(_YES_NO_STARTERS):
        return sentence

    lower_sentence = sentence.lower()
    lead_in = "No" if any(neg in lower_sentence for neg in _NEGATION_WORDS) else "Yes"

    first_word, _, rest = sentence.partition(" ")
    if first_word.isupper() and len(first_word) > 1:
        lowered_first_word = first_word
    else:
        lowered_first_word = first_word[:1].lower() + first_word[1:]

    return f"{lead_in}, {lowered_first_word} {rest}".strip() if rest else f"{lead_in}, {lowered_first_word}"


def _extract_grounded_answer(question: str, title: str, content: str) -> str:
    text = _strip_title_prefix(title, " ".join(content.strip().split()))
    sentence = _best_sentence(question, text)
    return _phrase_naturally(question, sentence)


def generate_answer(question: str, matches: list[dict[str, Any]]) -> str:
    context = "\n\n".join(match["content"] for match in matches)
    prompt = _build_prompt(question, context)

    if settings.llm_api_key:
        try:
            return _call_openai(prompt)
        except Exception as exc:  # noqa: BLE001 - missing package, bad key, network, etc.
            logger.warning("Cloud LLM call failed, falling back to Ollama: %s", exc)

    try:
        return _call_ollama(prompt)
    except Exception as exc:  # noqa: BLE001 - Ollama not running, times out, etc.
        logger.warning("Falling back to deterministic grounded extraction: %s", exc)

    for match in matches:
        if len(match["content"].split()) > 4:
            return _extract_grounded_answer(question, match["title"], match["content"])
    return _extract_grounded_answer(question, matches[0]["title"], matches[0]["content"])
