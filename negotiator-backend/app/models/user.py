# app/models/user.py
from sqlalchemy import Column, String, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100))
    hashed_password = Column(String(255), nullable=True)

    # Onboarding (FR-6, FR-7, FR-8)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    directions = Column(JSON, default=list)          # e.g. ["management", "hiring"]
    experience_level = Column(String(20), default="beginner")  # beginner | practitioner | expert

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    sessions = relationship("NegotiationSession", back_populates="user")