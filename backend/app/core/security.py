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

Staff Lease Management feature: `hash_password`/`verify_password` and
`require_staff` back a real login (see services/auth_service.py), ported
from teammate feature-lavanya's branch. Staff/admin already bypass the
per-guest ownership check below (global access - property managers aren't
scoped to one property), so no separate per-owner authorization helper is
needed.
"""

from __future__ import annotations

import bcrypt
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
    unit_id: UUID | None = None


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def create_access_token(guest_id: UUID, role: str = "resident", unit_id: UUID | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"guest_id": str(guest_id), "role": role, "exp": expire}
    if unit_id is not None:
        payload["unit_id"] = str(unit_id)
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
        raw_unit_id = payload.get("unit_id")
    except (JWTError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
        )

    try:
        guest_id = UUID(raw_guest_id)
        unit_id = UUID(raw_unit_id) if raw_unit_id is not None else None
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
        )

    return CurrentUser(guest_id=guest_id, role=role, unit_id=unit_id)


def require_staff(current_user: CurrentUser = Depends(get_current_guest_id)) -> CurrentUser:
    """Staff Lease Management feature - matches feature-lavanya's
    require_staff semantics: staff/admin only, global (not scoped to a
    single property)."""
    if current_user.role not in ("staff", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "FORBIDDEN", "message": "Staff or admin role required."},
        )
    return current_user


def require_resident(current_user: CurrentUser = Depends(get_current_guest_id)) -> CurrentUser:
    """AI Assistant feature - resident-only, mirroring require_staff's
    shape in the other direction (staff/admin get a 403)."""
    if current_user.role != "resident":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "FORBIDDEN", "message": "Resident role required."},
        )
    return current_user


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
