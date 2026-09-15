from __future__ import annotations

import uuid
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk

NO_ANSWER_MESSAGE = "I can't find this in the lease or building policy documents."


def _normalize_question(question: str) -> str:
    return " ".join(question.strip().split())


def _fetch_chunks() -> list[tuple[DocumentChunk, Document]]:
    db = SessionLocal()
    try:
        statement = select(DocumentChunk, Document).join(Document, DocumentChunk.document_id == Document.id)
        rows = db.execute(statement).all()
        return [(chunk, document) for chunk, document in rows]
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


def _extract_grounded_answer(question: str, chunk: DocumentChunk, document: Document) -> str:
    text = " ".join(chunk.content.strip().split())
    lower_question = question.lower()

    if "parking" in lower_question:
        if "included" in text.lower() or "one vehicle" in text.lower():
            return text
        return f"According to {document.title}, {text}"

    if "early termination" in lower_question or "termination" in lower_question:
        if "60 days" in text.lower() or "written notice" in text.lower():
            return text
        return f"According to the lease terms, {text}"

    return text


def _call_openai(question: str, context: str, settings) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.llm_api_key)
    prompt = (
        "Context:\n"
        f"{context}\n\n"
        f"Question: {question}\n\n"
        "Answer the question using ONLY the context above. Do not use any outside "
        "knowledge or make assumptions beyond what is stated in the context. If the "
        f"context does not answer the question, respond exactly with: \"{NO_ANSWER_MESSAGE}\""
    )
    response = client.responses.create(
        model=settings.llm_model or "gpt-5-nano",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a resident assistant for Meridian Residences. You must answer "
                    "strictly using only the context provided in the user message."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    answer = response.output_text
    if not answer or not answer.strip():
        raise ValueError("Empty response from LLM")
    return answer.strip()


def generate_answer(question: str, matches: list[dict[str, Any]]) -> str:
    settings = get_settings()
    if settings.llm_api_key:
        context = "\n\n".join(match["content"] for match in matches)
        try:
            return _call_openai(question, context, settings)
        except Exception:
            pass
    # Fallback: prefer the first match with substantive content over a bare header chunk.
    for match in matches:
        if len(match["content"].split()) > 4:
            return _extract_grounded_answer(question, match["chunk"], match["document"])
    return _extract_grounded_answer(question, matches[0]["chunk"], matches[0]["document"])


def _question_topic(question: str) -> str | None:
    lower = question.lower()
    if any(token in lower for token in ["parking", "vehicle", "guest parking", "fee", "monthly fee", "apartment parking"]):
        return "parking"
    if any(token in lower for token in ["lease", "termination", "notice", "security deposit", "move-out", "move out"]):
        return "lease"
    if any(token in lower for token in ["pet", "pets", "dog", "dogs", "cat", "cats", "animal"]):
        return "pets"
    if any(token in lower for token in ["quiet hours", "noise", "quiet hour"]):
        return "quiet_hours"
    return None


def retrieve_relevant_chunks(question: str, limit: int = 3) -> list[dict[str, Any]]:
    normalized = _normalize_question(question)
    if not normalized:
        return []

    topic = _question_topic(normalized)
    if not topic:
        return []

    ranked = _score_query_against_chunks(normalized, _fetch_chunks())
    filtered = [entry for entry in ranked if entry["score"] >= 0.08]

    results: list[dict[str, Any]] = []
    for entry in filtered[:limit]:
        chunk = entry["chunk"]
        document = entry["document"]
        results.append(
            {
                "document_id": document.id,
                "title": document.title,
                "chunk_id": chunk.id,
                "score": entry["score"],
                "content": chunk.content,
                "chunk": chunk,
                "document": document,
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
            "answer": "I cannot find this in the lease or building policy documents. Please contact the resident office for more detail.",
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
