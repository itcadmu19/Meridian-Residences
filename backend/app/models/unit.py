"""
Team 5 entity (Project Design Document section 5.3). Owned by the lease
story - the case brief refers to a unit in LeaseAgreement and
MaintenanceTicket, so this is the concrete resource behind those references.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("property_id", "unit_number"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("properties.id"), nullable=False
    )
    unit_number: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # available|occupied|maintenance
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    property: Mapped["Property"] = relationship(lazy="joined")
