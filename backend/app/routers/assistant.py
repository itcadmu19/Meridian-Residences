from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.assistant import ChatRequest
from app.services.assistant_service import handle_chat

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat")
def chat_with_assistant(payload: ChatRequest, db: Session = Depends(get_db)) -> JSONResponse:
    request_id = str(uuid.uuid4())
    try:
        result = handle_chat(payload.message, payload.conversation_id)
    except ValueError as exc:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "data": None,
                "message": str(exc),
                "error_code": "VALIDATION_ERROR",
                "meta": {"request_id": request_id},
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "answer": result["answer"],
                "sources": result["sources"],
                "conversation_id": result["conversation_id"],
            },
            "message": None,
            "meta": {"request_id": request_id},
        },
    )
