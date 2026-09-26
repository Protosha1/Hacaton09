# app/schemas/skill.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional


class SkillItem(BaseModel):
    """One metric row."""
    metric: str            # emotion_control | batna | spin
    current_value: int     # 0-100
    sessions_count: int
    history: Optional[List[int]] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserSkillsResponse(BaseModel):
    """All skills for a user. Always returns all 3 metrics, even if 0."""
    user_id: str
    skills: List[SkillItem]