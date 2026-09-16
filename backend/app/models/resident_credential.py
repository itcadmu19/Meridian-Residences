"""
Auth credential store - ported from teammate feature-lavanya's branch
(Story 3) so staff login uses the same shape the team already agreed on,
rather than a second bespoke auth model. Adapted to this branch's stack:
GUID() column type and jose-based JWT (app/core/security.py) instead of
PyJWT, but the table shape and role semantics are unchanged.

One row per person who can log in (resident or staff/admin), tied to a
guest_id + unit_id - see feature-lavanya's original docstring: "Lightweight
auth store scoped to unblock Story 3 authorization."
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import GUID


class ResidentCredential(Base):
    __tablename__ = "resident_credentials"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    guest_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("guests.id"), nullable=False, unique=True
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("units.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="resident")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
