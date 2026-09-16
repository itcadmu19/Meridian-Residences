"""
AI Assistant chat schemas - ported from teammate feature-Sanjana's branch,
adapted to reuse this app's SuccessResponse/Meta envelope (schemas/common.py)
instead of her manually-constructed JSONResponse bodies.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(..., description="Resident question")
    conversation_id: str | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        if value is None or not value.strip():
            raise ValueError("Question is required.")
        return value.strip()

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return None
        return value


class SourceResponse(BaseModel):
    document_id: str
    title: str
    chunk_id: str


class ChatDataResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    conversation_id: str
