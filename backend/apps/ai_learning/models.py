"""AI Learning Intelligence models.

This app is an *intelligence layer*: it reads from progress / academics /
assessment (single sources of truth) and materializes derived, AI-facing records
(weak topics, recommendations, study plans). It does not own curriculum,
attempts, or raw progress.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class MasteryBand(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    DEVELOPING = "developing", "Developing"
    PROFICIENT = "proficient", "Proficient"
    MASTERED = "mastered", "Mastered"


class LearningProfile(models.Model):
    """Per-learner AI profile: cached aggregates + study preferences."""

    class Pace(models.TextChoices):
        SLOW = "slow", "Slow"
        STEADY = "steady", "Steady"
        FAST = "fast", "Fast"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="learning_profile")

    overall_mastery = models.FloatField(default=0.0)         # 0..100
    topics_tracked = models.PositiveIntegerField(default=0)
    weak_topic_count = models.PositiveIntegerField(default=0)
    pace = models.CharField(max_length=10, choices=Pace.choices, default=Pace.STEADY)

    # Preferences that drive the scheduler.
    preferred_study_time = models.TimeField(default="20:00")
    daily_minutes_target = models.PositiveIntegerField(default=60)

    last_computed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"LearningProfile(user={self.user_id}, mastery={self.overall_mastery:.0f})"


class WeakTopic(models.Model):
    """Materialized weak-topic record (0–100 score) computed from progress."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_weak_topics")
    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="ai_weak_for")

    weak_score = models.FloatField(default=0.0)   # 0..100, higher = weaker
    mastery = models.FloatField(default=0.0)       # 0..100 snapshot
    accuracy = models.FloatField(default=0.0)      # 0..1 snapshot
    band = models.CharField(max_length=12, choices=MasteryBand.choices, default=MasteryBand.BEGINNER)
    reason = models.CharField(max_length=255, blank=True, default="")

    computed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "topic")
        ordering = ["-weak_score"]
        indexes = [models.Index(fields=["user", "-weak_score"])]

    def __str__(self) -> str:
        return f"WeakTopic(u={self.user_id}, t={self.topic_id}, {self.weak_score:.0f})"


class StudyRecommendation(models.Model):
    class Kind(models.TextChoices):
        LEARN = "learn", "Learn"
        REVISE = "revise", "Revise"
        PRACTICE = "practice", "Practice"
        PREREQUISITE = "prerequisite", "Prerequisite"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DONE = "done", "Done"
        DISMISSED = "dismissed", "Dismissed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_recommendations")
    topic = models.ForeignKey(
        "academics.Topic", on_delete=models.CASCADE, null=True, blank=True, related_name="ai_recommendations"
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    title = models.CharField(max_length=160)
    message = models.CharField(max_length=400, blank=True, default="")
    priority = models.PositiveIntegerField(default=0)   # higher = more important
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-priority", "id"]
        indexes = [models.Index(fields=["user", "status", "-priority"])]

    def __str__(self) -> str:
        return f"Rec({self.kind}: {self.title})"


class StudyPlan(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="study_plans")
    date = models.DateField(default=timezone.localdate)
    total_minutes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    generated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date"]
        indexes = [models.Index(fields=["user", "-date"])]

    def __str__(self) -> str:
        return f"StudyPlan(u={self.user_id}, {self.date})"


class StudySession(models.Model):
    """A single scheduled block inside a StudyPlan."""

    class Activity(models.TextChoices):
        REVISION = "revision", "Revision"
        QUIZ = "quiz", "Quiz"
        PRACTICE = "practice", "Practice"
        NOTES = "notes", "Notes"

    plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name="sessions")
    topic = models.ForeignKey(
        "academics.Topic", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_sessions"
    )
    order = models.PositiveIntegerField(default=0)
    start_time = models.TimeField()
    duration_min = models.PositiveIntegerField(default=30)
    activity_type = models.CharField(max_length=12, choices=Activity.choices, default=Activity.REVISION)
    title = models.CharField(max_length=160)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "start_time"]

    def __str__(self) -> str:
        return f"Session({self.activity_type} @ {self.start_time})"


class RecommendationLog(models.Model):
    """Audit trail of AI generation runs (for debugging/analytics)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_rec_logs")
    source = models.CharField(max_length=64, default="generate")
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]
