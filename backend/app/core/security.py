"""
JWT verification and resident-authorization helpers.

NOTE (Member 1 / lease story): shared/team-agreement file per contract
section 25 - proposed here because every lease/invoice/maintenance endpoint
needs identity resolution and none existed yet.

Scope note: this module only *verifies* tokens and centralizes the
"can this resident see this lease" check (contract section 16). It does not
issue tokens - no story in the ownership matrix currently owns a login
endpoint. `create_access_token` below exists only so tests (and whichever
story ends up owning login) have a single, contract-consistent way to mint
a token; it is not wired to any HTTP route.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    guest_id: UUID
    role: str = "resident"


def create_access_token(guest_id: UUID, role: str = "resident") -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"guest_id": str(guest_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_guest_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """Resolve the authenticated resident from the bearer token only.

    Per contract section 16: never trust a guest_id supplied by the browser
    (path/query/body) as the only authorization check - identity always
    comes from here.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        raw_guest_id = payload["guest_id"]
        role = payload.get("role", "resident")
    except (JWTError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
        )

    try:
        guest_id = UUID(raw_guest_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
        )

    return CurrentUser(guest_id=guest_id, role=role)


def authorize_lease_access(lease, current_user: CurrentUser) -> None:
    """Central IDOR check for every lease-owning endpoint (section 16.3).

    Returns a uniform 404 for both "not found" and "found but not yours" -
    see the plan's Decision 5 for why 404 was chosen over 403. Staff/admin
    roles bypass the ownership check but are still centralized here.
    """
    if lease is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "LEASE_NOT_FOUND", "message": "Lease not found."},
        )

    if current_user.role in ("staff", "admin"):
        return

    if lease.guest_id != current_user.guest_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "LEASE_NOT_FOUND", "message": "Lease not found."},
        )
