# app/core/xp.py
"""
XP calculation and rank system (FR-39, FR-40, FR-41, FR-42).
"""
from typing import Optional


# =========================
# Ranks (FR-39)
# =========================

RANKS = [
    {"level": 1, "name": "Ученик школы диалога", "min_xp": 0,    "max_xp": 100},
    {"level": 2, "name": "Мастер тактики",        "min_xp": 100,  "max_xp": 400},
    {"level": 3, "name": "Хищник аргументов",     "min_xp": 400,  "max_xp": 700},
    {"level": 4, "name": "Властелин аргументов",  "min_xp": 700,  "max_xp": 1200},
]


def get_rank(total_xp: int) -> dict:
    """
    Return the rank for a given total XP.
    Ranks: 1 (0-100), 2 (100-400), 3 (400-700), 4 (700+).
    """
    if total_xp is None or total_xp < 0:
        total_xp = 0
    for rank in RANKS:
        if total_xp < rank["max_xp"]:
            return rank
    return RANKS[-1]


def get_next_rank(total_xp: int) -> Optional[dict]:
    """Return the next rank (for progress bar), or None if max."""
    current = get_rank(total_xp)
    if current["level"] == RANKS[-1]["level"]:
        return None
    return RANKS[current["level"]]


# =========================
# XP calculation (FR-40, FR-41)
# =========================

BASE_XP = {
    "beginner": 50,
    "practitioner": 100,
    "expert": 200,
}

VERDICT_MULTIPLIER = {
    "yes": 1.0,       # success
    "partial": 0.6,   # partial
    "no": 0.2,        # failure
}

PERFECT_BONUS_XP = 50
PERFECT_SCORE_THRESHOLD = 80


def is_perfect_run(scores: dict) -> bool:
    """
    'Perfect run' = all 5 numeric scores >= 80.
    Used for the +50 XP bonus on expert difficulty (FR-41).
    """
    keys = [
        "argumentation_score",
        "objection_handling_score",
        "spin_score",
        "batna_score",
        "emotion_control_score",
    ]
    values = [scores.get(k, 0) for k in keys]
    return all(v >= PERFECT_SCORE_THRESHOLD for v in values)


def calculate_xp(difficulty: str, verdict: str, perfect: bool = False) -> int:
    """
    Calculate XP earned for one session.

    Formula: base(difficulty) × multiplier(verdict)
    Bonus: +50 XP if verdict=yes AND difficulty=expert AND perfect=True.
    """
    base = BASE_XP.get(difficulty, BASE_XP["beginner"])
    multiplier = VERDICT_MULTIPLIER.get(verdict, 0.2)
    xp = int(round(base * multiplier))

    if verdict == "yes" and difficulty == "expert" and perfect:
        xp += PERFECT_BONUS_XP

    return xp