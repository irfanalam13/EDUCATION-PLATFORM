"""Rank and materialize personalized study recommendations.

Inputs: weak topics (detector), spaced-repetition due-state (forgetting curve),
question availability (assessment), and curriculum order (academics) for
prerequisite hints.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.ai_learning.models import StudyRecommendation
from apps.ai_learning.services import forgetting_curve
from apps.ai_learning.services.weak_topic_detector import detect_weak_topics


def _topics_with_questions(topic_ids: list[int]) -> set[int]:
    if not topic_ids:
        return set()
    from apps.assessment.models import MCQQuestion

    return set(
        MCQQuestion.objects.filter(topic_id__in=topic_ids, is_active=True)
        .values_list("topic_id", flat=True)
        .distinct()
    )


def _prerequisite_hints(user, limit: int = 3) -> list[dict]:
    """Within each subject, flag studying ahead while an earlier topic is weak."""
    from apps.progress.models import TopicProgress

    rows = list(
        TopicProgress.objects.filter(user=user)
        .select_related("topic", "topic__chapter", "topic__chapter__subject")
        .order_by("topic__chapter__subject_id", "topic__chapter__number", "topic__order")
    )
    hints = []
    by_subject: dict[int, list] = {}
    for tp in rows:
        sid = tp.topic.chapter.subject_id if tp.topic.chapter else 0
        by_subject.setdefault(sid, []).append(tp)

    for ordered in by_subject.values():
        for i in range(1, len(ordered)):
            earlier, later = ordered[i - 1], ordered[i]
            if earlier.mastery < 50 and later.attempts > 0 and later.mastery <= earlier.mastery + 10:
                hints.append(
                    {
                        "topic": earlier.topic,
                        "title": f"Study {earlier.topic.title} before {later.topic.title}",
                        "message": "Strengthen the foundation topic first for faster progress.",
                        "priority": 70 + int(50 - earlier.mastery),
                    }
                )
                if len(hints) >= limit:
                    return hints
    return hints


@transaction.atomic
def generate_recommendations(user, *, top_n: int = 12) -> list[StudyRecommendation]:
    now = timezone.now()
    weak = detect_weak_topics(user)
    weak_topic_ids = [w.topic_id for w in weak]
    with_q = _topics_with_questions(weak_topic_ids)

    # topic_id -> best candidate dict
    candidates: dict[int, dict] = {}

    def offer(topic, kind, title, message, priority):
        key = topic.id if topic else f"_{kind}_{title}"
        prev = candidates.get(key)
        if prev is None or priority > prev["priority"]:
            candidates[key] = {
                "topic": topic, "kind": kind, "title": title,
                "message": message, "priority": int(priority),
            }

    # 1) Due-for-review (spaced repetition).
    from apps.progress.models import TopicProgress
    for tp in TopicProgress.objects.filter(user=user).select_related("topic"):
        if forgetting_curve.is_due(tp, now=now):
            days = forgetting_curve.days_to_target(tp)
            offer(
                tp.topic, StudyRecommendation.Kind.REVISE,
                f"Revise {tp.topic.title}",
                f"Review is due — ~{days} day(s) of practice to solidify it.",
                88 + (100 - tp.mastery) * 0.1,
            )

    # 2) Weak topics → practice (if questions exist) else revise.
    for w in weak:
        if w.topic_id in with_q:
            offer(
                w.topic, StudyRecommendation.Kind.PRACTICE,
                f"Practice {w.topic.title} MCQs",
                w.reason, w.weak_score,
            )
        else:
            offer(
                w.topic, StudyRecommendation.Kind.REVISE,
                f"Revise {w.topic.title}",
                w.reason, max(0, w.weak_score - 5),
            )

    # 3) Prerequisite hints.
    for h in _prerequisite_hints(user):
        offer(h["topic"], StudyRecommendation.Kind.PREREQUISITE, h["title"], h["message"], h["priority"])

    ranked = sorted(candidates.values(), key=lambda c: c["priority"], reverse=True)[:top_n]

    # Replace pending recommendations with the fresh set.
    StudyRecommendation.objects.filter(user=user, status=StudyRecommendation.Status.PENDING).delete()
    created = [
        StudyRecommendation.objects.create(
            user=user, topic=c["topic"], kind=c["kind"], title=c["title"],
            message=c["message"], priority=c["priority"],
        )
        for c in ranked
    ]
    return created
