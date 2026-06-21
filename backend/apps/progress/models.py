from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class TopicProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topic_progress")
    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="progress")

    attempts = models.PositiveIntegerField(default=0)
    correct = models.PositiveIntegerField(default=0)
    total_answered = models.PositiveIntegerField(default=0)

    easy_answered = models.PositiveIntegerField(default=0)
    medium_answered = models.PositiveIntegerField(default=0)
    hard_answered = models.PositiveIntegerField(default=0)

    last_score = models.PositiveIntegerField(default=0)
    last_total = models.PositiveIntegerField(default=0)

    mastery = models.FloatField(default=0.0)     # 0-100
    confidence = models.FloatField(default=0.0)  # 0-1
    last_practiced_at = models.DateTimeField(null=True, blank=True)

    # Spaced repetition
    next_review_at = models.DateTimeField(null=True, blank=True)
    interval_days = models.PositiveIntegerField(default=1)
    ease = models.FloatField(default=2.3)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "topic")
        indexes = [
            models.Index(fields=["user", "topic"]),
            models.Index(fields=["user", "mastery"]),
            models.Index(fields=["user", "next_review_at"]),
        ]

    @property
    def accuracy(self) -> float:
        return (self.correct / self.total_answered) if self.total_answered else 0.0


class DailyActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_activity")
    date = models.DateField(default=timezone.localdate)

    minutes = models.PositiveIntegerField(default=0)
    attempted = models.PositiveIntegerField(default=0)
    correct = models.PositiveIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "date")
        indexes = [models.Index(fields=["user", "date"])]


class StudyStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="study_streak")

    current_streak = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)


class WeakTopicCache(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weak_topics")
    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="weak_for_users")
    weakness_score = models.FloatField(default=0.0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "topic")
        indexes = [models.Index(fields=["user", "-weakness_score"])]


class UserGoal(models.Model):
    """
    Real-life feature: users set goals.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="goal")
    daily_minutes_goal = models.PositiveIntegerField(default=20)
    daily_attempt_goal = models.PositiveIntegerField(default=20)
    weekly_topics_mastered_goal = models.PositiveIntegerField(default=5)

    updated_at = models.DateTimeField(auto_now=True)


class ProgressSnapshot(models.Model):
    """
    Fast charts: store periodic snapshots (weekly recommended).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress_snapshots")
    date = models.DateField()  # snapshot date (e.g., each Sunday)

    topics = models.PositiveIntegerField(default=0)
    total_answered = models.PositiveIntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    avg_mastery = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "date")
        indexes = [models.Index(fields=["user", "date"])]
        # NOTE: institution/cohort models removed — institutions are owned solely
        # by the institutions app (single source of truth).


