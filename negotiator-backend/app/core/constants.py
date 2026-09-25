# app/core/constants.py
"""
Single source of truth for enums and constants used across the project.
Prevents string typos and makes refactoring easier.
"""

# =========================
# User roles
# =========================
class UserRole:
    USER = "user"
    ADMIN = "admin"
    ALL = {USER, ADMIN}


# =========================
# User statuses (v8)
# =========================
class UserStatus:
    PENDING_ONBOARDING = "pending_onboarding"
    ACTIVE = "active"
    ALL = {PENDING_ONBOARDING, ACTIVE}


# =========================
# Scenario statuses (admin)
# =========================
class ScenarioStatus:
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"
    ALL = {DRAFT, READY, ARCHIVED}


# =========================
# Negotiation session statuses
# =========================
# v8 formal lifecycle: created -> briefing_ready -> in_progress -> completed -> analyzed
# Our simplified mapping:
#   ongoing     == in_progress
#   finished    == completed + analyzed
#   interrupted == interrupted
class SessionStatus:
    ONGOING = "ongoing"
    FINISHED = "finished"
    INTERRUPTED = "interrupted"
    ALL = {ONGOING, FINISHED, INTERRUPTED}


# =========================
# Skill metrics
# =========================
class SkillMetric:
    EMOTION_CONTROL = "emotion_control"
    BATNA = "batna"
    SPIN = "spin"
    ALL = [EMOTION_CONTROL, BATNA, SPIN]  # ordered


# =========================
# Directions (categories in onboarding)
# =========================
class Direction:
    MANAGEMENT = "management"
    HIRING = "hiring"
    TEAM = "team"
    COLLEAGUES = "colleagues"
    CLIENTS = "clients"
    PARTNERS = "partners"
    ALL = {MANAGEMENT, HIRING, TEAM, COLLEAGUES, CLIENTS, PARTNERS}


# =========================
# Difficulty levels
# =========================
class Difficulty:
    BEGINNER = "beginner"
    PRACTITIONER = "practitioner"
    EXPERT = "expert"
    ALL = {BEGINNER, PRACTITIONER, EXPERT}


# =========================
# Relationship levels (FR-26)
# =========================
class Relationship:
    STRANGER = "stranger"
    COLLEAGUE = "colleague"
    FRIEND = "friend"
    BOSS = "boss"
    SUBORDINATE = "subordinate"
    ALL = {STRANGER, COLLEAGUE, FRIEND, BOSS, SUBORDINATE}


# =========================
# Power balance (FR-26)
# =========================
class PowerBalance:
    USER_STRONG = "user_strong"
    EQUAL = "equal"
    OPPONENT_STRONG = "opponent_strong"
    ALL = {USER_STRONG, EQUAL, OPPONENT_STRONG}


# =========================
# Verdict (analysis)
# =========================
class Verdict:
    SUCCESS = "yes"
    PARTIAL = "partial"
    FAILURE = "no"
    ALL = {SUCCESS, PARTIAL, FAILURE}


# =========================
# Transcript annotation types
# =========================
class AnnotationType:
    STRONG = "strong"
    NEUTRAL = "neutral"
    WEAK = "weak"
    ALL = {STRONG, NEUTRAL, WEAK}