# app/models/scenario.py
from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from app.db.session import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String(50), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Default negotiation context (FR-12)
    default_relationship = Column(String(30), nullable=True)
    default_power_balance = Column(String(30), nullable=True)

    user_role = Column(String(50))
    user_goal = Column(Text)

    opponent_role = Column(String(50))
    opponent_character = Column(Text)
    opponent_goal = Column(Text)
    opponent_interests = Column(JSON)
    opponent_constraints = Column(JSON)
    opponent_red_lines = Column(JSON)

    concession_limits = Column(JSON)
    tactics = Column(JSON)
    communication_style = Column(Text)

    # FR-46: tone/behavior and non-standard case (admin-created)
    tone_behavior = Column(Text, nullable=True)
    non_standard_case = Column(Text, nullable=True)

    # FR-43, FR-47: admin ownership and status
    admin_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(20), default="ready", nullable=False, index=True)
    # status values: draft | ready | archived

    # FR-48: invite code (unique, generated on publish)
    invite_code = Column(String(50), nullable=True, unique=True, index=True)

    initial_message = Column(Text)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])