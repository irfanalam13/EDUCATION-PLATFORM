# apps/gamification/selectors.py
from __future__ import annotations

from apps.gamification.models import LeaderboardEntry


def get_leaderboard(scope: str, period: str, scope_id: str = "", limit: int = 50):
    # period_key must match how it’s computed in services
    from apps.gamification.services.leaderboards import _period_key
    key = _period_key(period)
    return (
        LeaderboardEntry.objects
        .select_related("user")
        .filter(scope=scope, scope_id=scope_id, period=period, period_key=key)
        .order_by("-xp_total", "updated_at")[:limit]
    )
