# app/models/scenario.py
from sqlalchemy import Column, String, Text, JSON, DateTime
from app.db.session import Base
from datetime import datetime, UTC
import uuid


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String(50), nullable=True, index=True)   # ← НОВОЕ ПОЛЕ
    name = Column(String(100), nullable=False)
    description = Column(Text)

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

    initial_message = Column(Text)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))