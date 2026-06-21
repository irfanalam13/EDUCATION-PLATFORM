# apps/gamification/rules.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

# XP sources used across your system (academics, mcq, assessment, etc.)
XP_SOURCES = {
    "lesson_complete": 20,
    "practice_correct": 5,
    "quiz_finish": 30,
    "daily_login": 10,
    "quest_claim": 0,  # usually quest reward awards xp, not the claim itself
}

# Daily caps per source (None = unlimited)
DAILY_CAPS = {
    "practice_correct": 200,   # 200 xp/day max from practice
    "quiz_finish": 300,
    "lesson_complete": 200,
    "daily_login": 10,         # once/day
}

# Levels: total XP required to reach that level
# Example: level 1 starts at 0, level 2 at 100, level 3 at 250, etc.
LEVEL_THRESHOLDS = [
    0,     # L1
    100,   # L2
    250,   # L3
    450,   # L4
    700,   # L5
    1000,  # L6
    1400,  # L7
    1850,  # L8
    2350,  # L9
    2900,  # L10
]

# Streak multipliers (optional)
def streak_multiplier(streak_days: int) -> Decimal:
    if streak_days >= 30:
        return Decimal("1.25")
    if streak_days >= 7:
        return Decimal("1.10")
    return Decimal("1.00")

# Badge definitions (lightweight; actual Badge rows can mirror these)
BADGE_RULES = [
    {"code": "first_xp", "type": "min_total_xp", "value": 1},
    {"code": "xp_1000", "type": "min_total_xp", "value": 1000},
    {"code": "streak_7", "type": "min_streak", "value": 7},
    {"code": "streak_30", "type": "min_streak", "value": 30},
]

# Leaderboard defaults
LEADERBOARD_PERIODS = ["weekly", "monthly", "all_time"]
LEADERBOARD_SCOPES = ["global"]  # extend later: institution/cohort
