from django.conf import settings
from django.db import models
from django.utils import timezone

from .bank import MCQQuestion, Difficulty


class QuizMode(models.TextChoices):
    PRACTICE = "PRACTICE", "Practice"
    EXAM = "EXAM", "Exam"


class SessionState(models.TextChoices):
    CREATED = "CREATED", "Created"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    FINISHED = "FINISHED", "Finished"


class QuizTemplate(models.Model):
    name = models.CharField(max_length=200)

    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    chapter = models.ForeignKey(
        "academics.Chapter", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    topic = models.ForeignKey(
        "academics.Topic", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    count = models.PositiveIntegerField(default=10)
    mode = models.CharField(max_length=20, choices=QuizMode.choices, default=QuizMode.PRACTICE)

    # store difficulty mix in JSON
    difficulty_mix = models.JSONField(default=dict, blank=True)  # e.g. {"EASY":0.3,"MEDIUM":0.5,"HARD":0.2}

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Template#{self.id} {self.name}"


class QuizSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_sessions")

    mode = models.CharField(max_length=20, choices=QuizMode.choices, default=QuizMode.PRACTICE)
    state = models.CharField(max_length=20, choices=SessionState.choices, default=SessionState.CREATED)

    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    chapter = models.ForeignKey(
        "academics.Chapter", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    topic = models.ForeignKey(
        "academics.Topic", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    requested_count = models.PositiveIntegerField(default=10)
    difficulty_mix = models.JSONField(default=dict, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        indexes = [models.Index(fields=["user", "state", "created_at"])]

    def mark_started(self):
        if not self.started_at:
            self.started_at = timezone.now()
        self.state = SessionState.IN_PROGRESS

    def mark_finished(self):
        if not self.finished_at:
            self.finished_at = timezone.now()
        self.state = SessionState.FINISHED

    def __str__(self):
        return f"Session#{self.id} {self.user_id} {self.state}"


class QuizSessionQuestion(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name="session_questions")
    question = models.ForeignKey(MCQQuestion, on_delete=models.CASCADE, related_name="in_sessions")

    order = models.PositiveIntegerField(default=0)

    selected_option_id = models.BigIntegerField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        unique_together = [("session", "question")]
        indexes = [models.Index(fields=["session", "order"])]

    def __str__(self):
        return f"SessionQ#{self.id} S{self.session_id} Q{self.question_id}"


class QuizResult(models.Model):
    session = models.OneToOneField(QuizSession, on_delete=models.CASCADE, related_name="result")

    total = models.PositiveIntegerField(default=0)
    correct = models.PositiveIntegerField(default=0)
    score = models.FloatField(default=0.0)
    percentage = models.FloatField(default=0.0)

    xp_awarded = models.PositiveIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-computed_at"]

    def __str__(self):
        return f"Result S{self.session_id} {self.correct}/{self.total}"
