# app/core/xp.py
"""
XP calculation and rank system (FR-39, FR-40, FR-41, FR-42).
"""
from typing import Optional


# =========================
# Ranks (FR-39)
# =========================

RANKS = [
    # Названия рангов записаны через \u-escape (а не литеральной кириллицей).
    # Причина: на боевой машине эти же строки приходят на фронт побитые
    # ("Ученик школы диалога" превращается в мойбейк), при этом сам файл,
    # который проверяется здесь, побайтово корректен в UTF-8. Значит где-то
    # между диском и раннтаймом (скорее всего — устаревший .pyc в
    # __pycache__, скомпилированный из более старой версии файла) кириллица
    # ловит "тихую" порчу кодировки. \u-escape состоит только из ASCII-
    # символов, поэтому НЕ зависит от того, как файл сохранён/прочитан/
    # закеширован — Python обязан развернуть его в те же самые кодовые
    # точки при любых обстоятельствах. Если после этой правки ранг всё
    # ещё бьётся — значит порча происходит не в этом файле, а на уровне
    # ответа/сети, и нужно смотреть дальше.
    {"level": 1, "name": "\u0423\u0447\u0435\u043d\u0438\u043a \u0448\u043a\u043e\u043b\u044b \u0434\u0438\u0430\u043b\u043e\u0433\u0430", "min_xp": 0,    "max_xp": 100},
    {"level": 2, "name": "\u041c\u0430\u0441\u0442\u0435\u0440 \u0442\u0430\u043a\u0442\u0438\u043a\u0438",        "min_xp": 100,  "max_xp": 400},
    {"level": 3, "name": "\u0425\u0438\u0449\u043d\u0438\u043a \u0430\u0440\u0433\u0443\u043c\u0435\u043d\u0442\u043e\u0432",     "min_xp": 400,  "max_xp": 700},
    {"level": 4, "name": "\u0412\u043b\u0430\u0441\u0442\u0435\u043b\u0438\u043d \u0430\u0440\u0433\u0443\u043c\u0435\u043d\u0442\u043e\u0432",  "min_xp": 700,  "max_xp": 1200},
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