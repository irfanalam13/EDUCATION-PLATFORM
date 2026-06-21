"""Celery orchestration for the AI learning engine."""
from __future__ import annotations

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Sum
from django.utils import timezone

from apps.ai_learning.models import LearningProfile, RecommendationLog, WeakTopic
from apps.ai_learning.services.mastery_calculator import overall_mastery, topic_mastery_rows
from apps.ai_learning.services.recommendation_engine import generate_recommendations
from apps.ai_learning.services.study_scheduler import build_study_plan

User = get_user_model()


def mastery_cache_key(user_id: int) -> str:
    return f"ai:mastery:{user_id}"


def _infer_pace(user) -> str:
    from apps.progress.models import DailyActivity

    since = timezone.localdate() - timezone.timedelta(days=7)
    attempted = (
        DailyActivity.objects.filter(user=user, date__gte=since).aggregate(s=Sum("attempted"))["s"] or 0
    )
    if attempted >= 70:
        return LearningProfile.Pace.FAST
    if attempted >= 21:
        return LearningProfile.Pace.STEADY
    return LearningProfile.Pace.SLOW


def refresh_profile(user) -> LearningProfile:
    rows = topic_mastery_rows(user)
    profile, _ = LearningProfile.objects.get_or_create(user=user)
    profile.overall_mastery = overall_mastery(user)
    profile.topics_tracked = len(rows)
    profile.pace = _infer_pace(user)
    profile.last_computed_at = timezone.now()
    profile.save()
    return profile


def generate_all(user, *, build_plan: bool = True) -> dict:
    """Full pipeline: profile → weak topics + recommendations → study plan."""
    profile = refresh_profile(user)
    recs = generate_recommendations(user)  # also recomputes WeakTopic rows
    weak_count = WeakTopic.objects.filter(user=user).count()
    profile.weak_topic_count = weak_count
    profile.save(update_fields=["weak_topic_count"])

    plan = build_study_plan(user) if build_plan else None
    cache.delete(mastery_cache_key(user.id))

    RecommendationLog.objects.create(
        user=user,
        source="generate_all",
        payload={
            "weak": weak_count,
            "recs": len(recs),
            "plan_sessions": plan.sessions.count() if plan else 0,
        },
    )
    return {"profile": profile, "recs": recs, "weak_count": weak_count, "plan": plan}


@shared_task
def generate_for_user(user_id: int, build_plan: bool = True) -> dict:
    user = User.objects.get(id=user_id)
    result = generate_all(user, build_plan=build_plan)
    return {"user_id": user_id, "weak": result["weak_count"], "recs": len(result["recs"])}
