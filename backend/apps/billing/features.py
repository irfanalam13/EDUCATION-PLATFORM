"""Canonical feature catalogue and tier → feature mapping.

The billing app is the single source of truth for *what each tier unlocks*.
``limit`` semantics for a feature:
  * ``0``  → granted and unlimited (boolean capability / unmetered)
  * ``> 0`` → granted but metered (quota per calendar month)
Absent from a tier's dict → not granted.
"""
from __future__ import annotations

# ---- Feature keys (stable identifiers stored on FeatureAccess.feature) -------
FEATURE_UNLIMITED_QUIZZES = "unlimited_quizzes"
FEATURE_BASIC_PROGRESS = "basic_progress"
FEATURE_ADVANCED_ANALYTICS = "advanced_analytics"
FEATURE_AI_RECOMMENDATIONS = "ai_recommendations"
FEATURE_AI_TUTOR = "ai_tutor"
FEATURE_STUDY_PLANS = "study_plans"
FEATURE_PREMIUM_CONTENT = "premium_content"
FEATURE_TEACHER_DASHBOARDS = "teacher_dashboards"
FEATURE_REPORTING = "reporting"
FEATURE_INSTITUTION_ANALYTICS = "institution_analytics"
FEATURE_ASSIGNMENT_MANAGEMENT = "assignment_management"

ALL_FEATURES = (
    FEATURE_UNLIMITED_QUIZZES,
    FEATURE_BASIC_PROGRESS,
    FEATURE_ADVANCED_ANALYTICS,
    FEATURE_AI_RECOMMENDATIONS,
    FEATURE_AI_TUTOR,
    FEATURE_STUDY_PLANS,
    FEATURE_PREMIUM_CONTENT,
    FEATURE_TEACHER_DASHBOARDS,
    FEATURE_REPORTING,
    FEATURE_INSTITUTION_ANALYTICS,
    FEATURE_ASSIGNMENT_MANAGEMENT,
)

FEATURE_LABELS = {
    FEATURE_UNLIMITED_QUIZZES: "Unlimited quizzes",
    FEATURE_BASIC_PROGRESS: "Basic progress tracking",
    FEATURE_ADVANCED_ANALYTICS: "Advanced analytics",
    FEATURE_AI_RECOMMENDATIONS: "AI recommendations",
    FEATURE_AI_TUTOR: "AI study assistant",
    FEATURE_STUDY_PLANS: "Personalised study plans",
    FEATURE_PREMIUM_CONTENT: "Premium content library",
    FEATURE_TEACHER_DASHBOARDS: "Teacher dashboards",
    FEATURE_REPORTING: "Reporting & exports",
    FEATURE_INSTITUTION_ANALYTICS: "Institution analytics",
    FEATURE_ASSIGNMENT_MANAGEMENT: "Assignment management",
}

# Free users get a metered monthly quiz allowance; paid tiers are unlimited.
FREE_MONTHLY_QUIZ_LIMIT = 10

_FREE = {
    FEATURE_BASIC_PROGRESS: 0,
    FEATURE_UNLIMITED_QUIZZES: FREE_MONTHLY_QUIZ_LIMIT,
}

_PREMIUM = {
    FEATURE_UNLIMITED_QUIZZES: 0,
    FEATURE_BASIC_PROGRESS: 0,
    FEATURE_ADVANCED_ANALYTICS: 0,
    FEATURE_AI_RECOMMENDATIONS: 0,
    FEATURE_AI_TUTOR: 0,
    FEATURE_STUDY_PLANS: 0,
    FEATURE_PREMIUM_CONTENT: 0,
}

_INSTITUTION = {
    **_PREMIUM,
    FEATURE_TEACHER_DASHBOARDS: 0,
    FEATURE_REPORTING: 0,
    FEATURE_INSTITUTION_ANALYTICS: 0,
    FEATURE_ASSIGNMENT_MANAGEMENT: 0,
}

# Keyed by Plan.Tier values ("FREE" / "PREMIUM" / "INSTITUTION").
TIER_FEATURES = {
    "FREE": _FREE,
    "PREMIUM": _PREMIUM,
    "INSTITUTION": _INSTITUTION,
}


def features_for_tier(tier) -> dict:
    """Return {feature_key: limit} for a plan tier. Unknown tiers -> Free."""
    return dict(TIER_FEATURES.get(str(tier), _FREE))


def tier_grants(tier, feature) -> bool:
    """Whether a tier includes a feature at all (ignores quota)."""
    return feature in TIER_FEATURES.get(str(tier), _FREE)
