"""
Maintenance ticket entity - ported from teammate feature-lavanya's branch
(Design Contract section 5.5, "Submit, Track & Triage Maintenance") for the
App-wide Login + Maintenance feature. Same columns/constraints as her
version, adapted to this branch's GUID() type (SQLite-compatible for tests)
and explicit created_at/updated_at (set by the service layer, matching
LeaseAgreement's convention) instead of Postgres server_default triggers.

`photo_data_url`/`triage_reason` were added later (Maintenance enhancements
ported from a newer copy of feature-lavanya's branch) - see migration
0009_add_maintenance_photo_and_triage_reason.py.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.types import GUID

ISSUE_TYPES = ("plumbing", "electrical", "hvac", "appliance", "general", "other")
PRIORITIES = ("low", "medium", "high", "urgent")
STATUSES = ("open", "assigned", "in_progress", "resolved", "cancelled")


class MaintenanceTicket(Base):
    __tablename__ = "maintenance_tickets"
    __table_args__ = (
        CheckConstraint(f"issue_type IN {ISSUE_TYPES}", name="ck_maintenance_tickets_issue_type"),
        CheckConstraint(f"priority IN {PRIORITIES}", name="ck_maintenance_tickets_priority"),
        CheckConstraint(f"status IN {STATUSES}", name="ck_maintenance_tickets_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    unit_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("units.id"), nullable=False, index=True)
    guest_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("guests.id"), nullable=False, index=True)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)
    vendor_queue: Mapped[str | None] = mapped_column(String(100), nullable=True)
    escalated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    photo_data_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    triage_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    unit: Mapped["Unit"] = relationship(lazy="joined")
    guest: Mapped["Guest"] = relationship(lazy="joined")
