"""
AI Assistant router - ported from teammate feature-Sanjana's branch,
adapted to require resident authentication (her branch had none - see the
plan) and to return this app's SuccessResponse envelope via HTTPException
(matching maintenance.py's style) instead of manually-built JSONResponse
objects.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import CurrentUser, require_resident
from app.schemas.assistant import ChatDataResponse, ChatRequest
from app.schemas.common import SuccessResponse
from app.services.assistant_service import handle_chat

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=SuccessResponse[ChatDataResponse])
def chat_with_assistant(
    payload: ChatRequest,
    current_user: CurrentUser = Depends(require_resident),
):
    try:
        result = handle_chat(payload.message, payload.conversation_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": str(exc), "error_code": "VALIDATION_ERROR"},
        ) from exc

    return SuccessResponse(data=ChatDataResponse.model_validate(result))
