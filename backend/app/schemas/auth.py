from pydantic import BaseModel
from uuid import UUID


class LoginRequest(BaseModel):
    email: str
    password: str


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


class CurrentUser(BaseModel):
    guest_id: UUID
    unit_id: UUID
    role: str
