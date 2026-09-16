"""
Shared baseline entity (Project Design Document section 5.1).

NOTE (Member 1 / lease story): kept minimal and read-only from the lease
story's point of view - see plan Decision 1. Only the frozen columns are
included. Note the column is `address`, not `location` - the local
frontend's demo data used `location`, which was a naming mismatch flagged
in the plan and must be fixed on the frontend side, not here.
"""

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.types import GUID


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String, nullable=True)
