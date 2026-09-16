"""
AI Assistant retrieval logic - ported near-verbatim from teammate
feature-Sanjana's branch (backend/app/services/assistant_service.py),
repointed at this app's Document/DocumentChunk models and SessionLocal.
Answer generation itself lives in app/ai/assistant_agent.py, following this
app's convention of keeping LLM-calling code under app/ai/ (see
invoice_insight_agent.py, maintenance_ai_agent.py).
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select

from app.ai.assistant_agent import NO_ANSWER_MESSAGE, generate_answer
from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk


def _normalize_question(question: str) -> str:
    return " ".join(question.strip().split())


# Below this many words, a chunk is almost certainly a leaked heading
# fragment (e.g. a document's title paragraph landing in its own chunk
# when the following paragraph was too long to merge with it during
# seeding) rather than real policy content. Such fragments can score
# deceptively high in TF-IDF - they share exact words with the question
# and have almost nothing else diluting the match - so they're excluded
# from the candidate pool entirely rather than left to compete on score.
MIN_CHUNK_WORDS = 8


def _fetch_chunks() -> list[tuple[DocumentChunk, Document]]:
    db = SessionLocal()
    try:
        statement = select(DocumentChunk, Document).join(Document, DocumentChunk.document_id == Document.id)
        rows = db.execute(statement).all()
        return [
            (chunk, document)
            for chunk, document in rows
            if len(chunk.content.split()) >= MIN_CHUNK_WORDS
        ]
    finally:
        db.close()


def _score_query_against_chunks(question: str, chunks: list[tuple[DocumentChunk, Document]]) -> list[dict[str, Any]]:
    if not chunks:
        return []

    corpus = [chunk.content for chunk, _ in chunks]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([question] + corpus)
    similarity_scores = cosine_similarity(matrix[0:1], matrix[1:])[0]

    ranked: list[dict[str, Any]] = []
    for idx, score in enumerate(similarity_scores):
        chunk, document = chunks[idx]
        ranked.append({"score": float(score), "chunk": chunk, "document": document})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def _question_topic(question: str) -> str | None:
    lower = question.lower()
    if any(token in lower for token in ["parking", "vehicle", "guest parking", "fee", "monthly fee", "apartment parking"]):
        return "parking"
    if any(
        token in lower
        for token in [
            "lease",
            "termination",
            "notice",
            "security deposit",
            "move-out",
            "move out",
            "renew",
            "renewal",
            "late fee",
            "due date",
            "payment",
            "monthly rent",
        ]
    ) or re.search(r"\brent\b", lower):
        return "lease"
    if any(token in lower for token in ["pet", "pets", "dog", "dogs", "cat", "cats", "animal"]):
        return "pets"
    if any(token in lower for token in ["quiet hours", "noise", "quiet hour"]):
        return "quiet_hours"
    return None


# Maps a classified topic to the document_type it lives under (see
# database/seed/seed_assistant_documents.py's DOCUMENT_DIRS). Used to keep
# TF-IDF scoring scoped to the right document family - without this, a
# question like "What is the early termination policy?" can incorrectly
# match a Building Policy chunk over the actual Lease Terms chunk, since a
# tiny corpus makes cross-topic word overlap (e.g. the word "policy" itself)
# outweigh the real content match.
_TOPIC_DOCUMENT_TYPES = {
    "parking": "building_policy",
    "pets": "building_policy",
    "quiet_hours": "building_policy",
    "lease": "lease_terms",
}


def retrieve_relevant_chunks(question: str, limit: int = 3) -> list[dict[str, Any]]:
    normalized = _normalize_question(question)
    if not normalized:
        return []

    topic = _question_topic(normalized)
    if not topic:
        return []

    document_type = _TOPIC_DOCUMENT_TYPES.get(topic)
    candidates = [
        (chunk, document)
        for chunk, document in _fetch_chunks()
        if document_type is None or document.document_type == document_type
    ]

    ranked = _score_query_against_chunks(normalized, candidates)
    # The topic keyword gate above plus the document_type scoping already
    # rule out cross-topic contamination, so this only needs to filter out
    # true zero/near-zero noise, not compete with an arbitrary cutoff - a
    # 0.08 threshold was rejecting legitimate matches (e.g. "terminate"
    # vs. the question's "termination" don't share a token, capping an
    # otherwise-correct chunk's score just under it).
    filtered = [entry for entry in ranked if entry["score"] >= 0.02]

    results: list[dict[str, Any]] = []
    for entry in filtered[:limit]:
        chunk = entry["chunk"]
        document = entry["document"]
        results.append(
            {
                "document_id": str(document.id),
                "title": document.title,
                "chunk_id": str(chunk.id),
                "score": entry["score"],
                "content": chunk.content,
            }
        )
    return results


def handle_chat(question: str, conversation_id: str | None = None) -> dict[str, Any]:
    normalized = _normalize_question(question)
    if not normalized:
        raise ValueError("Question is required.")

    matches = retrieve_relevant_chunks(normalized)
    if not matches:
        return {
            "answer": NO_ANSWER_MESSAGE,
            "sources": [],
            "conversation_id": conversation_id or str(uuid.uuid4()),
        }

    answer = generate_answer(normalized, matches)
    sources = [
        {
            "document_id": match["document_id"],
            "title": match["title"],
            "chunk_id": match["chunk_id"],
        }
        for match in matches
    ]

    return {
        "answer": answer,
        "sources": sources,
        "conversation_id": conversation_id or str(uuid.uuid4()),
    }
