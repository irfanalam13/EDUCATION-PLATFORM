# apps/gamification/tasks.py
from __future__ import annotations
from celery import shared_task
from django.contrib.auth import get_user_model

from apps.gamification.services.badges import evaluate_badges
from apps.gamification.services.leaderboards import update_leaderboards
from apps.gamification.services.quests import update_quests_progress

User = get_user_model()


@shared_task
def award_badges_async(user_id: int, event: dict | None = None) -> dict:
    user = User.objects.get(id=user_id)
    newly = evaluate_badges(user)
    return {"awarded": newly}


@shared_task
def update_leaderboards_async(user_id: int, xp_delta: int, payload: dict | None = None) -> dict:
    payload = payload or {}
    scope = payload.get("scope", "global")
    scope_id = payload.get("scope_id", "")
    user = User.objects.get(id=user_id)
    update_leaderboards(user, int(xp_delta), scope=scope, scope_id=scope_id)
    return {"ok": True}


@shared_task
def update_quests_progress_async(user_id: int, payload: dict) -> dict:
    user = User.objects.get(id=user_id)
    source = payload.get("source", "")
    delta = int(payload.get("delta", 0))
    update_quests_progress(user, source=source, delta=delta)
    return {"ok": True}
