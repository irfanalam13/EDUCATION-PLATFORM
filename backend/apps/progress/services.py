# apps/progress/services.py
from dataclasses import dataclass
from django.db import transaction
from django.utils import timezone

from .models import TopicProgress, DailyActivity, StudyStreak
from datetime import timedelta


@dataclass
class DifficultyMix:
    easy: int = 0
    medium: int = 0
    hard: int = 0


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _compute_mastery(prev_mastery: float, score: int, total: int, mix: DifficultyMix) -> float:
    if total <= 0:
        return prev_mastery

    acc = score / total  # 0..1
    # difficulty weight: hard matters more. When no difficulty mix is supplied,
    # use a neutral weight of 1.0 (otherwise the weight collapses to 0 and
    # mastery can never rise).
    mix_total = mix.easy + mix.medium + mix.hard
    if mix_total <= 0:
        difficulty_weight = 1.0
    else:
        difficulty_weight = (mix.easy * 1.0 + mix.medium * 1.2 + mix.hard * 1.5) / mix_total

    target = acc * 100.0 * difficulty_weight
    target = _clamp(target, 0.0, 100.0)

    # EMA: smooth updates (realistic)
    alpha = 0.20
    new_mastery = (1 - alpha) * prev_mastery + alpha * target
    return _clamp(new_mastery, 0.0, 100.0)


def _apply_decay(mastery: float, last_practiced_at):
    """
    Optional: decay mastery slowly after inactivity.
    """
    if not last_practiced_at:
        return mastery
    days = (timezone.now() - last_practiced_at).days
    if days <= 7:
        return mastery
    # after a week, decay 0.5 per day up to -15 max
    decay = min(15.0, (days - 7) * 0.5)
    return _clamp(mastery - decay, 0.0, 100.0)


@transaction.atomic
def update_topic_progress(user, topic, score: int, total: int, difficulty_mix: dict | None = None):
    mix = DifficultyMix(**(difficulty_mix or {}))

    obj, _ = TopicProgress.objects.select_for_update().get_or_create(user=user, topic=topic)

    # Step 1 updates
    obj.attempts += 1
    obj.correct += int(score)
    obj.total_answered += int(total)

    obj.easy_answered += int(mix.easy)
    obj.medium_answered += int(mix.medium)
    obj.hard_answered += int(mix.hard)

    obj.last_score = int(score)
    obj.last_total = int(total)

    # Step 2 mastery
    prev = _apply_decay(obj.mastery, obj.last_practiced_at)
    obj.mastery = _compute_mastery(prev, score, total, mix)

    # confidence grows with attempts (bounded)
    obj.confidence = _clamp(obj.confidence + 0.05, 0.0, 1.0)

    obj.last_practiced_at = timezone.now()
    obj.save(update_fields=[
        "attempts", "correct", "total_answered",
        "easy_answered", "medium_answered", "hard_answered",
        "last_score", "last_total",
        "mastery", "confidence", "last_practiced_at", "updated_at"
    ])
    quiz_accuracy = (score / total) if total else 0.0
    _schedule_next_review(obj, quiz_accuracy)

    obj.save(update_fields=[
        "attempts", "correct", "total_answered",
        "easy_answered", "medium_answered", "hard_answered",
        "last_score", "last_total",
        "mastery", "confidence", "last_practiced_at",
        "next_review_at", "interval_days", "ease",
        "updated_at",
    ])

    # Refresh the user's weak-topic cache after this transaction commits, so the
    # async task never observes a half-written row (and never rolls XP back).
    def _recompute():
        from apps.progress.tasks import recompute_weak_topics_for_user
        recompute_weak_topics_for_user.delay(user.id)

    transaction.on_commit(_recompute)

    return obj


@transaction.atomic
def update_daily_activity(user, minutes: int = 0, attempted: int = 0, correct: int = 0, xp: int = 0, date=None):
    date = date or timezone.localdate()
    obj, _ = DailyActivity.objects.select_for_update().get_or_create(user=user, date=date)

    obj.minutes += int(minutes)
    obj.attempted += int(attempted)
    obj.correct += int(correct)
    obj.xp_earned += int(xp)
    obj.save()
    return obj


@transaction.atomic
def update_streak(user, date=None):
    date = date or timezone.localdate()
    obj, _ = StudyStreak.objects.select_for_update().get_or_create(user=user)

    if obj.last_active_date is None:
        obj.current_streak = 1
    else:
        delta = (date - obj.last_active_date).days
        if delta == 0:
            # already counted today
            pass
        elif delta == 1:
            obj.current_streak += 1
        else:
            obj.current_streak = 1

    obj.last_active_date = date
    obj.best_streak = max(obj.best_streak, obj.current_streak)
    obj.save()
    return obj




def _schedule_next_review(obj: TopicProgress, quiz_accuracy: float):
    """
    Simple spaced repetition:
    - good accuracy => interval grows
    - poor accuracy => reset interval
    """
    now = timezone.now()

    # base rules
    if quiz_accuracy >= 0.85:
        obj.interval_days = max(1, int(obj.interval_days * obj.ease))
        obj.ease = _clamp(obj.ease + 0.05, 1.3, 2.8)
    elif quiz_accuracy >= 0.60:
        obj.interval_days = max(1, int(obj.interval_days * 1.4))
        obj.ease = _clamp(obj.ease, 1.3, 2.8)
    else:
        obj.interval_days = 1
        obj.ease = _clamp(obj.ease - 0.10, 1.3, 2.8)

    obj.next_review_at = now + timedelta(days=obj.interval_days)
