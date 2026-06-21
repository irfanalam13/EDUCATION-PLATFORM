from datetime import timedelta
from django.utils import timezone
from .models import TopicProgress, DailyActivity, WeakTopicCache, StudyStreak, ProgressSnapshot

def get_due_topics(user, limit=20):
    now = timezone.now()
    return (TopicProgress.objects
            .filter(user=user, next_review_at__isnull=False, next_review_at__lte=now)
            .select_related("topic")
            .order_by("next_review_at")[:limit])

def get_activity_range(user, days=7):
    today = timezone.localdate()
    start = today - timedelta(days=days-1)
    return DailyActivity.objects.filter(user=user, date__gte=start, date__lte=today).order_by("date")

def get_weak_topics(user, limit=10):
    return WeakTopicCache.objects.filter(user=user).order_by("-weakness_score")[:limit]

def get_snapshots(user, from_date=None, to_date=None):
    qs = ProgressSnapshot.objects.filter(user=user).order_by("date")
    if from_date:
        qs = qs.filter(date__gte=from_date)
    if to_date:
        qs = qs.filter(date__lte=to_date)
    return qs
