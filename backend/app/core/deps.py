import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.schemas.auth import CurrentUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid or expired token", "error_code": "INVALID_TOKEN"},
        )

    return CurrentUser(guest_id=payload["guest_id"], unit_id=payload["unit_id"], role=payload["role"])


def require_staff(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role not in ("staff", "admin"):
        raise HTTPException(
            status_code=403,
            detail={"message": "Staff/admin role required", "error_code": "FORBIDDEN"},
        )
    return current_user
