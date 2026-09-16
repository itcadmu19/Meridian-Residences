"""
Seed data for the AI Assistant feature - lease/policy reference documents,
chunked for retrieval. Ported from teammate feature-Sanjana's branch
(backend/app/seed.py), adapted to this app's SessionLocal/models and to the
per-record idempotency convention used by seed_lease_story.py (skip a
document whose title already exists, rather than wiping and reseeding
everything on every run).

Run from backend/ with the venv active and DATABASE_URL set, e.g.:

    DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/meridian_residences \
        python ../database/seed/seed_assistant_documents.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.core.database import SessionLocal  # noqa: E402
from app.models.document import Document, DocumentChunk  # noqa: E402

DOC_ROOT = Path(__file__).resolve().parents[2] / "backend" / "documents"

DOCUMENT_DIRS = {
    "building_policy": DOC_ROOT / "building_policies",
    "lease_terms": DOC_ROOT / "lease_terms",
}


def _chunk_text(text: str, chunk_size: int = 300) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n+", text) if paragraph.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) <= chunk_size:
            current = (current + " " + paragraph).strip()
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks


def seed_documents() -> None:
    db = SessionLocal()
    try:
        for document_type, directory in DOCUMENT_DIRS.items():
            if not directory.exists():
                continue
            for file_path in sorted(directory.glob("*.txt")):
                title = file_path.stem.replace("_", " ").title()
                if db.query(Document).filter(Document.title == title).first():
                    continue

                text = file_path.read_text(encoding="utf-8").strip()
                if not text:
                    continue

                document = Document(
                    title=title,
                    document_type=document_type,
                    source_path=str(file_path),
                    version="1.0",
                )
                db.add(document)
                db.flush()

                for index, chunk_text in enumerate(_chunk_text(text)):
                    db.add(
                        DocumentChunk(
                            document_id=document.id,
                            chunk_index=index,
                            content=chunk_text,
                            chunk_metadata={"source_file": file_path.name},
                        )
                    )
                db.commit()
                print(f"Seeded document: {title}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_documents()
