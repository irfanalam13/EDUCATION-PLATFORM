"""Celery tasks: persist a daily metrics snapshot per institution for history."""
from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from apps.institutions.models import Institution

from . import services
from .models import InstitutionDailySnapshot


@shared_task(ignore_result=True)
def snapshot_institutions() -> int:
    """Upsert today's snapshot for every active institution. Run daily via beat."""
    today = timezone.localdate()
    count = 0
    for institution_id in Institution.objects.filter(is_active=True).values_list("id", flat=True):
        data = services.institution_overview(institution_id, days=1)
        m = data["metrics"]
        InstitutionDailySnapshot.objects.update_or_create(
            institution_id=institution_id,
            date=today,
            defaults={
                "active_students": m["active_students"],
                "daily_active_users": m["daily_active_users"],
                "learning_minutes": int(round(m["learning_hours"] * 60)),
                "avg_quiz_score": m["quiz_performance"],
                "assignment_completion_rate": m["assignments"]["completion_rate"],
                "avg_mastery": m["avg_mastery"],
            },
        )
        count += 1
    return count
