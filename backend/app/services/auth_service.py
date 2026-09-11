import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models.resident_credential import ResidentCredential
from app.schemas.auth import TokenResponse

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    pass


def login(db: Session, email: str, password: str) -> TokenResponse:
    normalized_email = email.strip().lower()
    credential = (
        db.query(ResidentCredential).filter(func.lower(ResidentCredential.email) == normalized_email).first()
    )

    # Same error for unknown email vs wrong password — do not reveal which one failed.
    if credential is None or not verify_password(password, credential.password_hash):
        logger.info("Failed login attempt for email=%s", normalized_email)
        raise InvalidCredentialsError("Invalid email or password")

    token = create_access_token(
        {"guest_id": str(credential.guest_id), "unit_id": str(credential.unit_id), "role": credential.role}
    )
    logger.info("Successful login for guest_id=%s", credential.guest_id)

    return TokenResponse(
        access_token=token,
        guest_id=credential.guest_id,
        unit_id=credential.unit_id,
        role=credential.role,
    )
