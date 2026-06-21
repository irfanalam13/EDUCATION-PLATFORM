"""Turn ranked recommendations into a timed daily study plan."""
from __future__ import annotations

import datetime as dt

from django.db import transaction
from django.utils import timezone

from apps.ai_learning.models import (
    LearningProfile, StudyPlan, StudySession, StudyRecommendation,
)

BLOCK_MINUTES = 30

_ACTIVITY_BY_KIND = {
    StudyRecommendation.Kind.PRACTICE: StudySession.Activity.QUIZ,
    StudyRecommendation.Kind.REVISE: StudySession.Activity.REVISION,
    StudyRecommendation.Kind.LEARN: StudySession.Activity.NOTES,
    StudyRecommendation.Kind.PREREQUISITE: StudySession.Activity.REVISION,
}


@transaction.atomic
def build_study_plan(user, *, date=None) -> StudyPlan:
    date = date or timezone.localdate()
    profile, _ = LearningProfile.objects.get_or_create(user=user)

    recs = list(
        StudyRecommendation.objects.filter(
            user=user, status=StudyRecommendation.Status.PENDING
        ).order_by("-priority")
    )

    max_blocks = max(1, profile.daily_minutes_target // BLOCK_MINUTES)
    chosen = recs[:max_blocks]

    # Rebuild the plan for this date.
    StudyPlan.objects.filter(user=user, date=date).delete()
    plan = StudyPlan.objects.create(
        user=user, date=date, generated_at=timezone.now(),
        total_minutes=len(chosen) * BLOCK_MINUTES,
    )

    base = dt.datetime.combine(date, profile.preferred_study_time)
    for i, rec in enumerate(chosen):
        start_time = (base + dt.timedelta(minutes=BLOCK_MINUTES * i)).time()
        StudySession.objects.create(
            plan=plan,
            topic=rec.topic,
            order=i,
            start_time=start_time,
            duration_min=BLOCK_MINUTES,
            activity_type=_ACTIVITY_BY_KIND.get(rec.kind, StudySession.Activity.REVISION),
            title=rec.title,
        )

    return plan
