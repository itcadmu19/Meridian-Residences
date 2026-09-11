from __future__ import annotations

import re
from pathlib import Path

from sqlalchemy import delete

from app.core.database import SessionLocal, init_db
from app.models.document import Document, DocumentChunk


DOC_ROOT = Path(__file__).resolve().parents[1] / "documents"


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


def _seed_document_file(document_type: str, file_path: Path) -> None:
    db = SessionLocal()
    try:
        text = file_path.read_text(encoding="utf-8")
        cleaned = text.strip()
        if not cleaned:
            return

        document = Document(
            title=file_path.stem.replace("_", " ").title(),
            document_type=document_type,
            source_path=str(file_path),
            version="1.0",
        )
        db.add(document)
        db.flush()

        for index, chunk_text in enumerate(_chunk_text(cleaned)):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk_text,
                    embedding=None,
                    metadata={"source_file": file_path.name},
                )
            )
        db.commit()
    finally:
        db.close()


def seed_database() -> None:
    init_db()

    db = SessionLocal()
    try:
        db.execute(delete(DocumentChunk))
        db.execute(delete(Document))
        db.commit()
    finally:
        db.close()

    document_dirs = {
        "building_policy": DOC_ROOT / "building_policies",
        "lease_terms": DOC_ROOT / "lease_terms",
    }

    for document_type, directory in document_dirs.items():
        if not directory.exists():
            continue
        for file_path in sorted(directory.glob("*.txt")):
            _seed_document_file(document_type, file_path)


if __name__ == "__main__":
    seed_database()
