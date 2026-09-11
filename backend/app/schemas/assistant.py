from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(..., description="Resident question")
    conversation_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        if value is None or not value.strip():
            raise ValueError("Question is required.")
        return value.strip()

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            return None
        return value


class SourceResponse(BaseModel):
    document_id: str
    title: str
    chunk_id: str


class AssistantDataResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    conversation_id: str


class ChatResponse(BaseModel):
    success: bool
    data: Optional[AssistantDataResponse] = None
    message: Optional[str] = None
    meta: dict
