# app/models/negotiation.py
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship as sa_relationship
from datetime import datetime, UTC
from app.db.session import Base
import uuid


class NegotiationSession(Base):
    __tablename__ = "negotiation_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario_id = Column(String(36), ForeignKey("scenarios.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    role = Column(String(50))
    goal = Column(Text)
    opponent = Column(String(50))
    difficulty = Column(String(20), default="practitioner", nullable=False)

    # Session context (FR-12)
    relationship = Column(String(30), nullable=True)
    power_balance = Column(String(30), nullable=True)

    status = Column(String(20), default="ongoing")

    agreed_price = Column(String(50), nullable=True)
    final_terms = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    finished_at = Column(DateTime, nullable=True)

    messages = sa_relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    user = sa_relationship("User", back_populates="sessions")
    scenario = sa_relationship("Scenario")
    analysis = sa_relationship(
        "AnalysisReport",
        back_populates="session",
        uselist=False,
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String(36),
        ForeignKey("negotiation_sessions.id"),
        nullable=False,
    )
    sender = Column(String(20))
    text = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))

    session = sa_relationship("NegotiationSession", back_populates="messages")