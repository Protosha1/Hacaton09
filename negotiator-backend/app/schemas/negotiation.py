# app/schemas/negotiation.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class StartNegotiationRequest(BaseModel):
    scenario_id: str = Field(..., examples=["scenario-1"])
    user_id: Optional[str] = Field(None, examples=["user-1"])
    difficulty: Optional[Literal["beginner", "practitioner", "expert"]] = Field(
        None, examples=["practitioner"],
    )
    relationship: Optional[Literal["stranger", "colleague", "friend", "boss", "subordinate"]] = Field(
        None, examples=["colleague"],
    )
    power_balance: Optional[Literal["user_strong", "equal", "opponent_strong"]] = Field(
        None, examples=["equal"],
    )


class MessageRequest(BaseModel):
    session_id: str = Field(..., examples=["5b7ba051-189b-4fe3-9f82-aebc28feedf1"])
    message: str = Field(..., examples=["Our price is $1200 per unit."])


class TranscriptAnnotation(BaseModel):
    """Annotation for one USER message in the dialogue."""
    index: int
    original: str
    type: Literal["strong", "neutral", "weak"]
    category: str
    why: str
    suggestion: Optional[str] = None


class AnalysisResponse(BaseModel):
    session_id: str
    goal_achieved: str
    argumentation_score: int
    objection_handling_score: int
    overall_score: int
    spin_score: Optional[int] = None
    batna_score: Optional[int] = None
    emotion_control_score: Optional[int] = None
    spin_analysis: Optional[str] = None
    batna_analysis: Optional[str] = None
    transcript_annotations: List[TranscriptAnnotation] = []
    strong_count: int = 0
    weak_count: int = 0
    neutral_count: int = 0
    xp_earned: int = 0
    is_perfect: bool = False
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    full_report: str


class SessionListItem(BaseModel):
    session_id: str
    scenario_id: Optional[str] = None
    scenario_name: Optional[str] = None
    role: Optional[str] = None
    goal: Optional[str] = None
    opponent: Optional[str] = None
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None
    overall_score: Optional[int] = None


class SessionMessageItem(BaseModel):
    sender: str
    text: str
    timestamp: datetime


class AnalysisListItem(BaseModel):
    session_id: str
    overall_score: int
    goal_achieved: str
    created_at: datetime


class InterruptedSessionInfo(BaseModel):
    session_id: str
    scenario_id: Optional[str] = None
    scenario_name: Optional[str] = None
    role: Optional[str] = None
    goal: Optional[str] = None
    difficulty: Optional[str] = None
    relationship: Optional[str] = None
    power_balance: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None
    messages_count: int = 0


class InterruptedSessionResponse(BaseModel):
    has_interrupted: bool
    session: Optional[InterruptedSessionInfo] = None

class BriefingResponse(BaseModel):
    """
    Public briefing data for a scenario (FR-15).
    No spoilers: does NOT include opponent_character, opponent_goal,
    tactics, concession_limits.
    """
    scenario_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    user_role: Optional[str] = None
    user_goal: Optional[str] = None
    opponent_role: Optional[str] = None
    initial_message: Optional[str] = None