# app/models/user_added_case.py
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from app.db.session import Base


class UserAddedCase(Base):
    """
    Tracks which user received which admin-created case via invite link
    (FR-7, FR-49). Used to build the personal "Added" category in Catalog.
    """
    __tablename__ = "user_added_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("scenarios.id"), nullable=False, index=True)
    added_at = Column(DateTime, default=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("user_id", "case_id", name="uq_user_added_case"),
    )

    user = relationship("User")
    case = relationship("Scenario")