import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.guest import Guest
from app.models.property import Property
from app.models.resident_credential import ResidentCredential
from app.models.unit import Unit
from app.schemas.auth import RegisterRequest, RegisterResponse, TokenResponse

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    pass


class EmailAlreadyExistsError(Exception):
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


def register(db: Session, payload: RegisterRequest) -> RegisterResponse:
    normalized_email = payload.email.strip().lower()
    if db.query(ResidentCredential).filter(func.lower(ResidentCredential.email) == normalized_email).first():
        raise EmailAlreadyExistsError("An account with this email already exists")

    role = payload.role.strip().lower() if payload.role else "resident"
    if role not in {"resident", "staff", "admin"}:
        role = "resident"

    property_name = (payload.property_name or "Meridian Residences").strip() or "Meridian Residences"
    property_row = db.query(Property).filter(func.lower(Property.name) == property_name.lower()).first()
    if property_row is None:
        property_row = Property(name=property_name, brand="Meridian", timezone="UTC")
        db.add(property_row)
        db.flush()

    unit_number = (payload.unit_number or ("STAFF-01" if role == "staff" else "101")).strip() or "101"
    unit = (
        db.query(Unit)
        .filter(Unit.property_id == property_row.id, func.lower(Unit.unit_number) == unit_number.lower())
        .first()
    )
    if unit is None:
        unit = Unit(
            property_id=property_row.id,
            unit_number=unit_number,
            unit_type=payload.unit_type or ("studio" if role == "staff" else "2BHK"),
            status="occupied",
        )
        db.add(unit)
        db.flush()

    guest = db.query(Guest).filter(func.lower(Guest.email) == normalized_email).first()
    if guest is None:
        guest = Guest(name=payload.name.strip() or "New Resident", email=normalized_email, phone=None, loyalty_tier="silver")
        db.add(guest)
        db.flush()

    credential = ResidentCredential(
        guest_id=guest.id,
        unit_id=unit.id,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        role=role,
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)

    token = create_access_token({"guest_id": str(credential.guest_id), "unit_id": str(credential.unit_id), "role": credential.role})

    logger.info("Registered new %s account for guest_id=%s", role, guest.id)
    return RegisterResponse(
        access_token=token,
        guest_id=credential.guest_id,
        unit_id=credential.unit_id,
        role=credential.role,
        email=credential.email,
        name=guest.name,
    )
