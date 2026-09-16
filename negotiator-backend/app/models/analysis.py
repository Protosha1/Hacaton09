# app/models/analysis.py
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, ForeignKey
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

    # Existing metrics
    goal_achieved = Column(String(20))
    argumentation_score = Column(Integer)
    objection_handling_score = Column(Integer)
    overall_score = Column(Integer)

    # NEW metrics (FR-10)
    spin_score = Column(Integer, nullable=True)         # SPIN methodology
    batna_score = Column(Integer, nullable=True)        # BATNA/Harvard method
    emotion_control_score = Column(Integer, nullable=True)  # Emotional control

    strengths = Column(JSON)
    weaknesses = Column(JSON)
    suggestions = Column(JSON)

    full_report = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    session = relationship("NegotiationSession", back_populates="analysis")