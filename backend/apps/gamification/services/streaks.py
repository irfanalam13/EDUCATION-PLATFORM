# apps/gamification/services/streaks.py
from __future__ import annotations
from django.db import transaction
from django.utils import timezone

from apps.gamification.models import UserGamificationProfile


@transaction.atomic
def touch_activity(user, activity_date=None) -> UserGamificationProfile:
    profile, _ = UserGamificationProfile.objects.select_for_update().get_or_create(user=user)

    today = activity_date or timezone.localdate()

    if profile.last_active_date == today:
        return profile

    if profile.last_active_date is None:
        profile.streak_days = 1
    else:
        delta = (today - profile.last_active_date).days
        if delta == 1:
            profile.streak_days += 1
        elif delta > 1:
            # streak broken
            profile.streak_days = 1

    if profile.streak_days > profile.longest_streak:
        profile.longest_streak = profile.streak_days

    profile.last_active_date = today
    profile.save(update_fields=["streak_days", "longest_streak", "last_active_date", "updated_at"])
    return profile
