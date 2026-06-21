"""Forgetting curve / spaced-repetition helpers.

Builds on the SM-2-style fields progress.TopicProgress already maintains
(interval_days, ease, next_review_at). We add an Ebbinghaus retention estimate
and a "days to reach target mastery" projection.
"""
from __future__ import annotations

import math

from django.utils import timezone


def retention(topic_progress, *, now=None) -> float:
    """Estimated probability the topic is still retained, 0..1.

    R = exp(-elapsed_days / strength), where memory strength grows with the
    spaced-repetition interval and ease factor.
    """
    now = now or timezone.now()
    last = topic_progress.last_practiced_at
    if not last:
        return 0.0
    elapsed_days = max(0.0, (now - last).total_seconds() / 86400.0)
    strength = max(1.0, float(topic_progress.interval_days) * float(topic_progress.ease))
    return round(math.exp(-elapsed_days / strength), 3)


def is_due(topic_progress, *, now=None, retention_floor: float = 0.6) -> bool:
    """Due if the scheduled review has passed OR estimated retention dropped low."""
    now = now or timezone.now()
    nra = topic_progress.next_review_at
    if nra is not None and nra <= now:
        return True
    return retention(topic_progress, now=now) < retention_floor


def days_to_target(topic_progress, *, target: float = 80.0) -> int:
    """Rough projection of study days to reach `target` mastery.

    Assumes each focused session lifts mastery by a gain proportional to current
    accuracy (a confident learner improves faster). Bounded for sanity.
    """
    mastery = float(topic_progress.mastery)
    if mastery >= target:
        return 0
    acc = float(topic_progress.accuracy)
    gain_per_session = max(4.0, 6.0 + acc * 12.0)  # 6..18 points/session
    sessions = math.ceil((target - mastery) / gain_per_session)
    return int(min(60, max(1, sessions)))
