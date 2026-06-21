# apps/gamification/services/badges.py
from __future__ import annotations

from django.db import transaction
from apps.gamification.models import Badge, UserBadge, UserGamificationProfile
from apps.gamification.rules import BADGE_RULES


@transaction.atomic
def ensure_badge_rows_exist() -> None:
    """
    One-time helper: sync DB badges with rulebook codes.
    """
    existing = set(Badge.objects.values_list("code", flat=True))
    for rule in BADGE_RULES:
        code = rule["code"]
        if code not in existing:
            Badge.objects.create(
                code=code,
                name=code.replace("_", " ").title(),
                description="",
                criteria=rule,
                is_active=True,
            )


@transaction.atomic
def evaluate_badges(user) -> list[str]:
    ensure_badge_rows_exist()

    profile, _ = UserGamificationProfile.objects.select_for_update().get_or_create(user=user)
    owned = set(UserBadge.objects.filter(user=user).values_list("badge__code", flat=True))

    newly = []
    for rule in BADGE_RULES:
        code = rule["code"]
        if code in owned:
            continue

        rtype = rule["type"]
        val = int(rule["value"])

        ok = False
        if rtype == "min_total_xp":
            ok = profile.total_xp >= val
        elif rtype == "min_streak":
            ok = profile.streak_days >= val

        if ok:
            badge = Badge.objects.get(code=code)
            UserBadge.objects.create(user=user, badge=badge, metadata={"awarded_by": "rulebook"})
            newly.append(code)
            _notify_badge_earned(user, badge)

    return newly


def _notify_badge_earned(user, badge) -> None:
    """Best-effort in-app notification when a badge is earned."""
    try:
        from apps.notifications.services import create_notification
        create_notification(
            user=user,
            title=f"New badge unlocked: {badge.name} 🏅",
            body=badge.description or "",
            type="BADGE",
            data={"event": "badge_earned", "badge_code": badge.code},
        )
    except Exception:
        pass
