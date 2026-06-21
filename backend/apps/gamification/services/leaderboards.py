# apps/gamification/services/leaderboards.py
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.gamification.models import LeaderboardEntry, UserGamificationProfile


def _period_key(period: str) -> str:
    today = timezone.localdate()
    if period == LeaderboardEntry.PERIOD_WEEKLY:
        year, week, _ = today.isocalendar()
        return f"{year}-W{week:02d}"
    if period == LeaderboardEntry.PERIOD_MONTHLY:
        return f"{today.year}-{today.month:02d}"
    return "all"


@transaction.atomic
def update_leaderboards(user, xp_delta: int, scope: str = "global", scope_id: str = "") -> None:
    profile, _ = UserGamificationProfile.objects.get_or_create(user=user)
    if xp_delta <= 0:
        return

    for period in [LeaderboardEntry.PERIOD_WEEKLY, LeaderboardEntry.PERIOD_MONTHLY, LeaderboardEntry.PERIOD_ALL_TIME]:
        key = _period_key(period)
        entry, _ = LeaderboardEntry.objects.select_for_update().get_or_create(
            user=user,
            scope=scope,
            scope_id=scope_id,
            period=period,
            period_key=key,
            defaults={"xp_total": 0},
        )
        entry.xp_total = entry.xp_total + xp_delta
        entry.save(update_fields=["xp_total", "updated_at"])
