import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

ISSUE_TYPES = ("plumbing", "electrical", "hvac", "appliance", "general", "other")
PRIORITIES = ("low", "medium", "high", "urgent")
STATUSES = ("open", "assigned", "in_progress", "resolved", "cancelled")


class MaintenanceTicket(Base):
    """Member 3 owned entity — Submit, Track & Triage Maintenance (Design Contract §5.5)."""

    __tablename__ = "maintenance_tickets"
    __table_args__ = (
        CheckConstraint(f"issue_type IN {ISSUE_TYPES}", name="ck_maintenance_tickets_issue_type"),
        CheckConstraint(f"priority IN {PRIORITIES}", name="ck_maintenance_tickets_priority"),
        CheckConstraint(f"status IN {STATUSES}", name="ck_maintenance_tickets_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    guest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guests.id"), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="open")
    vendor_queue: Mapped[str | None] = mapped_column(String(100))
    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    unit: Mapped["Unit"] = relationship(back_populates="maintenance_tickets")  # noqa: F821
    guest: Mapped["Guest"] = relationship(back_populates="maintenance_tickets")  # noqa: F821
