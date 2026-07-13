from celery import shared_task
from django.utils import timezone
from django.db.models import Avg, Sum, Count

from .models import TopicProgress, WeakTopicCache, ProgressSnapshot

@shared_task
def recompute_weak_topics_for_user(user_id: int, top_n: int = 20):
    qs = TopicProgress.objects.filter(user_id=user_id, total_answered__gte=10)
    now = timezone.now()

    rows = []
    for tp in qs:
        acc = tp.accuracy
        days_inactive = (now - tp.last_practiced_at).days if tp.last_practiced_at else 999
        decay_bonus = min(30, max(0, days_inactive - 7))  # 0..30

        weakness = (100 - tp.mastery) * 0.6 + (1 - acc) * 100 * 0.3 + decay_bonus * 0.1
        rows.append((tp.topic_id, float(weakness)))

    rows.sort(key=lambda x: x[1], reverse=True)
    rows = rows[:top_n]

    keep = []
    for topic_id, w in rows:
        keep.append(topic_id)
        WeakTopicCache.objects.update_or_create(
            user_id=user_id,
            topic_id=topic_id,
            defaults={"weakness_score": w},
        )

    WeakTopicCache.objects.filter(user_id=user_id).exclude(topic_id__in=keep).delete()
    return {"user_id": user_id, "count": len(keep)}

@shared_task
def create_weekly_snapshot_for_user(user_id: int, date_str: str | None = None):
    """
    date_str optional in YYYY-MM-DD; if None use today.
    You can call this every Sunday.
    """
    date = timezone.localdate() if not date_str else timezone.datetime.fromisoformat(date_str).date()

    agg = TopicProgress.objects.filter(user_id=user_id).aggregate(
        topics=Count("id"),
        total_answered=Sum("total_answered"),
        correct=Sum("correct"),
        avg_mastery=Avg("mastery"),
    )
    total_answered = int(agg["total_answered"] or 0)
    correct = int(agg["correct"] or 0)
    accuracy = (correct / total_answered) if total_answered else 0.0

    ProgressSnapshot.objects.update_or_create(
        user_id=user_id,
        date=date,
        defaults={
            "topics": int(agg["topics"] or 0),
            "total_answered": total_answered,
            "accuracy": float(accuracy),
            "avg_mastery": float(agg["avg_mastery"] or 0.0),
        }
    )
    return {"user_id": user_id, "date": str(date)}
