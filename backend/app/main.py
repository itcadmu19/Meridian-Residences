"""
FastAPI application entrypoint.

NOTE (Member 1 / lease story): shared/team-agreement file per contract
section 25 - proposed here as the initial skeleton since nothing existed
yet and the Lease story builds first in the frozen integration sequence
(section 26). Register your own router the same way `leases.router` is
registered below; please review before merging.
"""

import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.routers import assistant, auth, dev_auth, invoices, leases, maintenance, staff_leases

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    return await call_next(request)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", None)
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message", "Request failed.")
        error_code = detail.get("error_code", "ERROR")
    else:
        message = str(detail)
        error_code = "ERROR"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": message,
            "error_code": error_code,
            "meta": {"request_id": request_id},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "message": "Invalid request.",
            "error_code": "VALIDATION_ERROR",
            "meta": {"request_id": request_id},
        },
    )


app.include_router(leases.router, prefix=settings.api_prefix)
app.include_router(dev_auth.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(staff_leases.router, prefix=settings.api_prefix)
app.include_router(invoices.router, prefix=settings.api_prefix)
app.include_router(maintenance.router, prefix=settings.api_prefix)
app.include_router(assistant.router, prefix=settings.api_prefix)


@app.get("/health")
def health_check():
    return {"status": "ok"}
