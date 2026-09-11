from pydantic import BaseModel
from uuid import UUID


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    guest_id: UUID
    unit_id: UUID
    role: str


class CurrentUser(BaseModel):
    guest_id: UUID
    unit_id: UUID
    role: str
