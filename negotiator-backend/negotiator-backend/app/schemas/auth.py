# app/schemas/auth.py
import re
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List, Literal


def _check_password_strength(v: str) -> str:
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    return v


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=8, examples=["Secret1234"])
    name: Optional[str] = Field(None, examples=["Ivan Petrov"])
    consent_given: bool = Field(
        True,
        description="User consents to personal data processing.",
        examples=[True],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return _check_password_strength(v)


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., examples=["Secret1234"])


class OnboardingRequest(BaseModel):
    directions: List[str] = Field(
        ..., min_length=1, max_length=3,
        examples=[["management", "hiring"]],
    )
    experience_level: Literal["beginner", "practitioner", "expert"] = Field(
        ..., examples=["beginner"],
    )


class AdminRegisterRequest(BaseModel):
    email: EmailStr = Field(..., examples=["admin@negotiator-ai.com"])
    password: str = Field(..., min_length=8, examples=["AdminPass123"])
    name: str = Field(..., examples=["Administrator"])
    consent_given: bool = Field(True, description="Consent to personal data processing.")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return _check_password_strength(v)


class AdminLoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["admin@negotiator-ai.com"])
    password: str = Field(..., examples=["AdminPass123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None       # FR-20
    role: str = "user"
    status: str = "pending_onboarding"
    onboarding_completed: bool
    directions: Optional[List[str]] = None
    experience_level: str
    total_xp: int = 0
    rank_level: int = 1
    rank_name: str = "Ученик школы диалога"
    consent_given: bool = False

    model_config = ConfigDict(from_attributes=True)