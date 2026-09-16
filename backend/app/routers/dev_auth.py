"""
Temporary, development-only convenience endpoint.

NOT part of the frozen API contract and NOT a real login story - no story
in the ownership matrix currently owns issuing JWTs (see the plan's
Decision 5 risk note). This exists only so the local frontend can be
exercised against the real backend without a real login flow. Gated to
APP_ENV=development so it doesn't exist outside local dev. Remove or
replace once the team decides who owns real authentication.

Staff Lease Management feature: staff use the real /auth/login endpoint
(see routers/auth.py) instead of a dev-token mint, since a real login now
exists for that persona.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.guest import Guest
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["dev-auth"])


@router.post("/dev-auth/token", response_model=SuccessResponse[dict])
def issue_dev_token(guest_id: UUID, db: Session = Depends(get_db)):
    if settings.app_env != "development":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    guest = db.get(Guest, guest_id)
    if guest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "GUEST_NOT_FOUND", "message": "Guest not found."},
        )

    token = create_access_token(guest_id)
    return SuccessResponse(data={"access_token": token, "guest_id": str(guest_id)})
