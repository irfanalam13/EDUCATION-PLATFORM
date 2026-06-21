# apps/gamification/services/quests.py
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.gamification.models import Quest, UserQuestProgress
from apps.gamification.services.xp import award_xp


@transaction.atomic
def update_quests_progress(user, source: str, delta: int) -> None:
    now = timezone.now()
    qs = Quest.objects.filter(is_active=True).exclude(start_at__gt=now).exclude(end_at__lt=now)

    for quest in qs:
        rules = quest.rules or {}
        if rules.get("source") != source:
            continue
        target = int(rules.get("target", 0))
        if target <= 0:
            continue

        row, _ = UserQuestProgress.objects.select_for_update().get_or_create(user=user, quest=quest)
        if row.is_completed:
            continue

        row.progress = min(target, row.progress + 1)  # increment by event count (not xp)
        if row.progress >= target:
            row.is_completed = True
        row.save(update_fields=["progress", "is_completed", "updated_at"])


@transaction.atomic
def claim_quest(user, quest: Quest) -> dict:
    row, _ = UserQuestProgress.objects.select_for_update().get_or_create(user=user, quest=quest)
    if not row.is_completed:
        return {"ok": False, "reason": "not_completed"}
    if row.is_claimed:
        return {"ok": False, "reason": "already_claimed"}

    reward = quest.reward or {}
    xp = int(reward.get("xp", 0))

    if xp > 0:
        # idempotency ties to quest claim
        award_xp(
            user=user,
            source="quest_claim",
            points=xp,
            metadata={"quest": quest.code},
            idempotency_key=f"quest:{quest.code}:claim",
            touch=False,
        )

    row.is_claimed = True
    row.save(update_fields=["is_claimed", "updated_at"])
    return {"ok": True, "reward": reward}
