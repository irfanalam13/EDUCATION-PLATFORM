# apps/progress/recommendations.py
from django.utils import timezone
from apps.progress.models import TopicProgress, WeakTopicCache

def build_recommendations(user, limit=10):
    """
    Priority:
    1) Due topics (spaced repetition)
    2) Weak topics (cached)
    3) Low mastery topics (fallback)
    Output: list of actions (topic_id + reason + suggested quiz config)
    """
    now = timezone.now()
    out = []
    used_topic_ids = set()

    # 1) Due
    due = (
        TopicProgress.objects.filter(user=user, next_review_at__isnull=False, next_review_at__lte=now)
        .select_related("topic")
        .order_by("next_review_at")[:limit]
    )
    for tp in due:
        used_topic_ids.add(tp.topic_id)
        out.append({
            "topic": tp.topic_id,
            "reason": "due_review",
            "mastery": float(tp.mastery),
            "suggested_quiz": {"count": 10, "mode": "mixed", "difficulty_mix": {"easy": 3, "medium": 5, "hard": 2}},
        })
        if len(out) >= limit:
            return out

    # 2) Weak cache
    weak = (
        WeakTopicCache.objects.filter(user=user)
        .select_related("topic")
        .order_by("-weakness_score")[:limit]
    )
    for w in weak:
        if w.topic_id in used_topic_ids:
            continue
        used_topic_ids.add(w.topic_id)
        out.append({
            "topic": w.topic_id,
            "reason": "weak_topic",
            "weakness_score": float(w.weakness_score),
            "suggested_quiz": {"count": 12, "mode": "focused", "difficulty_mix": {"easy": 4, "medium": 6, "hard": 2}},
        })
        if len(out) >= limit:
            return out

    # 3) Low mastery fallback
    low = (
        TopicProgress.objects.filter(user=user)
        .exclude(topic_id__in=used_topic_ids)
        .order_by("mastery")[:limit]
    )
    for tp in low:
        out.append({
            "topic": tp.topic_id,
            "reason": "low_mastery",
            "mastery": float(tp.mastery),
            "suggested_quiz": {"count": 10, "mode": "focused", "difficulty_mix": {"easy": 5, "medium": 4, "hard": 1}},
        })
        if len(out) >= limit:
            return out

    return out
