# app/models/skill_progress.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid

from app.db.session import Base


class SkillProgress(Base):
    """
    Aggregated skill metrics per user (FR-24).
    One row per (user_id, metric).

    Metrics:
      - emotion_control
      - batna
      - spin

    Formula for updating:
      new_value = old_value * 0.7 + session_score * 0.3
    """
    __tablename__ = "skill_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    metric = Column(String(30), nullable=False, index=True)
    current_value = Column(Integer, default=0, nullable=False)
    sessions_count = Column(Integer, default=0, nullable=False)
    history = Column(JSON, default=list)  # list[int]  last N values
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC),
                        onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("user_id", "metric", name="uq_user_metric"),
    )