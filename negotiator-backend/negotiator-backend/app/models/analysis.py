# app/models/analysis.py
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.db.session import Base
import uuid


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String(36),
        ForeignKey("negotiation_sessions.id"),
        unique=True,
        nullable=False,
    )

    # Core verdict & metrics
    goal_achieved = Column(String(20))
    argumentation_score = Column(Integer)
    objection_handling_score = Column(Integer)
    overall_score = Column(Integer)

    # v8 methodology metrics (numbers)
    spin_score = Column(Integer, nullable=True)
    batna_score = Column(Integer, nullable=True)
    emotion_control_score = Column(Integer, nullable=True)

    # v8 methodology analysis (text blocks, FR-20, FR-36)
    spin_analysis = Column(Text, nullable=True)
    batna_analysis = Column(Text, nullable=True)

    # Full transcript annotations (FR-21, FR-37)
    # List of {index, original, type, category, why, suggestion}
    transcript_annotations = Column(JSON, nullable=True)

    # XP
    xp_earned = Column(Integer, default=0, nullable=False)
    is_perfect = Column(Boolean, default=False, nullable=False)

    strengths = Column(JSON)
    weaknesses = Column(JSON)
    suggestions = Column(JSON)
    full_report = Column(Text)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    session = relationship("NegotiationSession", back_populates="analysis")