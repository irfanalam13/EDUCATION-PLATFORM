"""Detect weak topics from progress data and materialize WeakTopic rows."""
from __future__ import annotations

from django.utils import timezone

from apps.ai_learning.models import WeakTopic
from apps.ai_learning.services.mastery_calculator import mastery_band


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def compute_weak_score(tp, *, now=None) -> tuple[float, str]:
    """Weakness 0..100 (higher = weaker) plus a human reason.

    Blends: how far below full mastery, how inaccurate, and decay from inactivity.
    """
    now = now or timezone.now()
    mastery_gap = 100.0 - float(tp.mastery)
    acc_gap = (1.0 - float(tp.accuracy)) * 100.0

    days_inactive = (now - tp.last_practiced_at).days if tp.last_practiced_at else 999
    decay = min(30.0, max(0.0, days_inactive - 7))  # 0..30 after a week idle

    score = _clamp(mastery_gap * 0.5 + acc_gap * 0.3 + decay * 0.2)

    # Dominant reason.
    if decay >= 15:
        reason = f"Not practiced in {days_inactive} days — likely fading."
    elif acc_gap >= 40:
        reason = f"Low accuracy ({tp.accuracy * 100:.0f}%) — concept needs work."
    elif mastery_gap >= 40:
        reason = "Mastery still developing — keep practicing."
    else:
        reason = "Almost there — a quick revision will help."
    return round(score, 1), reason


def detect_weak_topics(user, *, min_attempts: int = 1, weak_threshold: float = 40.0, top_n: int = 50):
    """Recompute the user's WeakTopic rows. Returns the kept WeakTopic list."""
    from apps.progress.models import TopicProgress

    now = timezone.now()
    qs = (
        TopicProgress.objects.filter(user=user, total_answered__gte=min_attempts)
        .select_related("topic")
    )

    scored = []
    for tp in qs:
        score, reason = compute_weak_score(tp, now=now)
        scored.append((tp, score, reason))

    scored.sort(key=lambda x: x[1], reverse=True)
    scored = [s for s in scored if s[1] >= weak_threshold][:top_n]

    kept_topic_ids = []
    for tp, score, reason in scored:
        kept_topic_ids.append(tp.topic_id)
        WeakTopic.objects.update_or_create(
            user=user,
            topic=tp.topic,
            defaults={
                "weak_score": score,
                "mastery": round(float(tp.mastery), 1),
                "accuracy": round(float(tp.accuracy), 3),
                "band": mastery_band(tp.mastery),
                "reason": reason,
                "computed_at": now,
            },
        )

    # Drop topics that are no longer weak.
    WeakTopic.objects.filter(user=user).exclude(topic_id__in=kept_topic_ids).delete()

    return list(
        WeakTopic.objects.filter(user=user).select_related("topic").order_by("-weak_score")
    )
