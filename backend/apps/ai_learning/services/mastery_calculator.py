"""Mastery banding + summaries derived from progress.TopicProgress."""
from __future__ import annotations

from apps.ai_learning.models import MasteryBand

# Thresholds on the 0..100 mastery scale produced by progress.services.
_BANDS = [
    (80.0, MasteryBand.MASTERED),
    (60.0, MasteryBand.PROFICIENT),
    (35.0, MasteryBand.DEVELOPING),
    (0.0, MasteryBand.BEGINNER),
]


def mastery_band(mastery: float) -> str:
    for threshold, band in _BANDS:
        if mastery >= threshold:
            return band
    return MasteryBand.BEGINNER


def topic_mastery_rows(user) -> list[dict]:
    """One row per topic the user has progress on, with band + scope labels."""
    from apps.progress.models import TopicProgress

    qs = (
        TopicProgress.objects.filter(user=user)
        .select_related("topic", "topic__chapter", "topic__chapter__subject")
        .order_by("topic__chapter__subject_id", "topic__chapter__number", "topic__order")
    )
    rows = []
    for tp in qs:
        topic = tp.topic
        chapter = topic.chapter
        subject = chapter.subject if chapter else None
        rows.append(
            {
                "topic_id": topic.id,
                "topic_title": topic.title,
                "chapter": chapter.title if chapter else "",
                "subject": subject.name if subject else "",
                "subject_id": subject.id if subject else None,
                "mastery": round(tp.mastery, 1),
                "accuracy": round(tp.accuracy, 3),
                "band": mastery_band(tp.mastery),
                "attempts": tp.attempts,
                "last_practiced_at": tp.last_practiced_at,
            }
        )
    return rows


def overall_mastery(user) -> float:
    from django.db.models import Avg
    from apps.progress.models import TopicProgress

    avg = TopicProgress.objects.filter(user=user).aggregate(a=Avg("mastery"))["a"]
    return round(float(avg or 0.0), 1)


def band_distribution(rows: list[dict]) -> dict[str, int]:
    dist = {b.value: 0 for b in MasteryBand}
    for r in rows:
        dist[r["band"]] = dist.get(r["band"], 0) + 1
    return dist
