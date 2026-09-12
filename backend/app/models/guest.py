"""
Shared baseline entity (Project Design Document section 5.1).

NOTE (Member 1 / lease story): kept minimal and read-only from the lease
story's point of view. Isolated in its own module (not inside a lease file)
so it can be reconciled with any teammate who already defined this
independently - see plan Decision 1. Only the frozen columns are included.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import GUID


class Guest(Base):
    __tablename__ = "guests"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    loyalty_tier: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
