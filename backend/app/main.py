import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, guests, invoices, leases, maintenance

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Member 3 — Maintenance router. Other members register their routers here too.
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(guests.router, prefix=settings.api_prefix)
app.include_router(leases.router, prefix=settings.api_prefix)
app.include_router(invoices.router, prefix=settings.api_prefix)
app.include_router(maintenance.router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {"success": True, "data": {"status": "ok"}}
