"""
Shared SQLAlchemy engine/session setup.

NOTE (Member 1 / lease story): shared/team-agreement file per contract
section 25 - proposed here as the initial skeleton since nothing existed
yet. One connection pattern for the whole app, as required by the contract.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
