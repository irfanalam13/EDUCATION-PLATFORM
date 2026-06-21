# apps/gamification/services/xp.py
from __future__ import annotations

from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.gamification.models import (
    UserGamificationProfile, UserLevel, XpTransaction, XpDailyCap
)
from apps.gamification.rules import DAILY_CAPS, streak_multiplier


def _apply_daily_caps(user, source: str, points: int) -> tuple[int, dict]:
    cap = DAILY_CAPS.get(source)
    if cap is None:
        return points, {"cap_applied": False, "cap_remaining": None}

    today = timezone.localdate()
    row, _ = XpDailyCap.objects.select_for_update().get_or_create(
        user=user, date=today, source=source, defaults={"used_points": 0}
    )
    remaining = max(0, cap - row.used_points)
    awarded = min(points, remaining)

    # consume
    row.used_points = row.used_points + max(0, awarded)
    row.save(update_fields=["used_points"])

    return awarded, {"cap_applied": True, "cap_remaining": remaining}


def _compute_level(total_xp: int) -> int:
    # simple rule: iterate thresholds from rules.py (store there)
    from apps.gamification.rules import LEVEL_THRESHOLDS

    lvl = 1
    for i, req in enumerate(LEVEL_THRESHOLDS, start=1):
        if total_xp >= req:
            lvl = i
    return lvl


@transaction.atomic
def award_xp(
    *,
    user,
    source: str,
    points: int,
    metadata: dict | None = None,
    idempotency_key: str = "",
    object_type: str = "",
    object_id: str = "",
    touch: bool = True,
) -> XpTransaction:
    """
    Single entrypoint for awarding XP.
    Use idempotency_key for retry-safety (critical in production).
    """
    metadata = metadata or {}

    # Ensure profile exists + lock for consistency
    profile, _ = UserGamificationProfile.objects.select_for_update().get_or_create(user=user)

    # Optional: update streak once/day (safe)
    if touch:
        from apps.gamification.services.streaks import touch_activity
        profile = touch_activity(user)

    # Idempotency: if already exists, return existing tx
    if idempotency_key:
        existing = XpTransaction.objects.filter(
            user=user, source=source, idempotency_key=idempotency_key
        ).first()
        if existing:
            return existing

    base_points = int(points)
    if base_points <= 0:
        # For now we only allow positive awards here; implement revert separately if needed.
        tx = XpTransaction.objects.create(
            user=user,
            source=source,
            object_type=object_type,
            object_id=object_id,
            points_base=base_points,
            points_awarded=0,
            multiplier=Decimal("1.00"),
            status=XpTransaction.STATUS_BLOCKED,
            idempotency_key=idempotency_key,
            metadata={**metadata, "reason": "non_positive_points"},
        )
        return tx

    # Apply caps first
    capped_points, cap_meta = _apply_daily_caps(user, source, base_points)
    if capped_points <= 0:
        tx = XpTransaction.objects.create(
            user=user,
            source=source,
            object_type=object_type,
            object_id=object_id,
            points_base=base_points,
            points_awarded=0,
            multiplier=Decimal("1.00"),
            status=XpTransaction.STATUS_BLOCKED,
            idempotency_key=idempotency_key,
            metadata={**metadata, **cap_meta, "reason": "daily_cap_reached"},
        )
        return tx

    # Multipliers (streak)
    mult = streak_multiplier(profile.streak_days)
    awarded = int(Decimal(capped_points) * mult)

    # Create tx
    tx = XpTransaction.objects.create(
        user=user,
        source=source,
        object_type=object_type,
        object_id=object_id,
        points_base=base_points,
        points_awarded=awarded,
        multiplier=mult,
        status=XpTransaction.STATUS_AWARDED,
        idempotency_key=idempotency_key,
        metadata={**metadata, **cap_meta},
    )

    # Update cached totals
    prev_level = profile.level
    profile.total_xp = profile.total_xp + max(0, awarded)
    new_level = _compute_level(profile.total_xp)
    profile.level = new_level
    profile.save(update_fields=["total_xp", "level", "updated_at"])

    # Keep UserLevel in sync (optional)
    ul, _ = UserLevel.objects.select_for_update().get_or_create(user=user)
    if ul.level != new_level:
        ul.level = new_level
        ul.save(update_fields=["level", "updated_at"])

    # Fire async follow-ups ONLY after the DB transaction commits. Doing this
    # inside the atomic block (as before) meant a broker hiccup raised inside the
    # transaction and rolled the whole XP award back. on_commit also guarantees
    # the workers read fully-committed rows.
    user_id = user.id

    def _fire_followups():
        from apps.gamification.tasks import (
            award_badges_async,
            update_leaderboards_async,
            update_quests_progress_async,
        )
        award_badges_async.delay(user_id, {"event": "xp_awarded", "source": source})
        update_leaderboards_async.delay(user_id, awarded, {"scope": "global"})
        update_quests_progress_async.delay(user_id, {"source": source, "delta": awarded})

    transaction.on_commit(_fire_followups)

    # Level-up notification (in-app). Best-effort: never let notification errors
    # break XP awarding.
    if new_level > prev_level:
        def _notify_level_up():
            try:
                from apps.notifications.services import create_notification
                create_notification(
                    user=user,
                    title=f"Level up! You reached level {new_level} 🎉",
                    body=f"You now have {profile.total_xp} XP.",
                    type="XP",
                    data={"event": "level_up", "level": new_level},
                )
            except Exception:
                pass

        transaction.on_commit(_notify_level_up)

    return tx
