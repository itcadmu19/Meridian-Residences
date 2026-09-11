from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import init_db
from app.routers.assistant import router as assistant_router
from app.seed import seed_database

settings = get_settings()

app = FastAPI(title=settings.app_name)

init_db()
seed_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    seed_database()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = str(uuid.uuid4())
    message = "Question is required."
    for error in exc.errors():
        error_message = str(error.get("msg", "")).lower()
        if "question is required" in error_message or "field required" in error_message or "value error" in error_message:
            message = "Question is required."
            break
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "message": message,
            "error_code": "VALIDATION_ERROR",
            "meta": {"request_id": request_id},
        },
    )


app.include_router(assistant_router, prefix=settings.api_prefix)
