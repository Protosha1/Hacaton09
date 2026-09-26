# app/models/user.py
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from app.db.session import Base
from app.core.constants import UserRole, UserStatus


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100))
    hashed_password = Column(String(255), nullable=True)

    # FR-20: avatar in profile header
    avatar_url = Column(String(500), nullable=True)

    # RBAC
    role = Column(String(20), default=UserRole.USER, nullable=False, index=True)

    # Status: pending_onboarding | active
    status = Column(String(30), default=UserStatus.PENDING_ONBOARDING, nullable=False, index=True)

    # Onboarding data
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    directions = Column(JSON, default=list)
    experience_level = Column(String(20), default="beginner")

    # XP / Ranks
    total_xp = Column(Integer, default=0, nullable=False)

    # Consent (v8 privacy)
    consent_given = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    sessions = relationship("NegotiationSession", back_populates="user")