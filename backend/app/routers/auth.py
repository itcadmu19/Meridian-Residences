from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services import auth_service
from app.services.auth_service import InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        return auth_service.login(db, payload.email, payload.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid email or password", "error_code": "INVALID_CREDENTIALS"},
        )
