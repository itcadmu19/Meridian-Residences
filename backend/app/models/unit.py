import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Unit(Base):
    """Team 5 shared entity (Design Contract §5.3). Read-only dependency for maintenance."""

    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("property_id", "unit_number", name="uq_units_property_unit_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    property_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    unit_number: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="available")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    maintenance_tickets: Mapped[list["MaintenanceTicket"]] = relationship(back_populates="unit")  # noqa: F821
