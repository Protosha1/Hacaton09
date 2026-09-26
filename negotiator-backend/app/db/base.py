# app/db/base.py
from app.db.session import Base

# Import all models so Alembic sees them
from app.models.user import User
from app.models.scenario import Scenario
from app.models.negotiation import NegotiationSession, Message
from app.models.analysis import AnalysisReport
from app.models.skill_progress import SkillProgress
from app.models.user_added_case import UserAddedCase

__all__ = [
    "Base",
    "User",
    "Scenario",
    "NegotiationSession",
    "Message",
    "AnalysisReport",
    "SkillProgress",
    "UserAddedCase",
]