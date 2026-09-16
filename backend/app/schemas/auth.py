"""
Auth schemas - ported from teammate feature-lavanya's branch. `unit_id` is
back in the response (App-wide Login feature): residents need it to file
maintenance tickets tied to their own unit.

`RegisterRequest`/`RegisterResponse` are the self-service Registration
feature, ported from a newer copy of her branch.
"""

from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str
    # Only used if this email has no account yet (see auth_service.login) -
    # matches the role tab the Sign In page's user selected, same as
    # Register.jsx's role selector. Ignored for an existing account.
    role: str = "resident"


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "resident"
    unit_number: str | None = None
    unit_type: str | None = None
    property_name: str = "Meridian Residences"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    guest_id: UUID
    unit_id: UUID
    role: str


class RegisterResponse(TokenResponse):
    email: str
    name: str
