from django.conf import settings
from django.db import models


class Difficulty(models.TextChoices):
    EASY = "EASY", "Easy"
    MEDIUM = "MEDIUM", "Medium"
    HARD = "HARD", "Hard"


class MCQQuestion(models.Model):
    """Canonical MCQ question. Scope references the academics hierarchy."""

    title = models.CharField(max_length=255, blank=True, default="")
    question_text = models.TextField()

    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="mcq_questions",
    )
    chapter = models.ForeignKey(
        "academics.Chapter", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="mcq_questions",
    )
    topic = models.ForeignKey(
        "academics.Topic", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="mcq_questions",
    )

    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )

    explanation = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mcq_questions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["topic", "difficulty", "is_active"]),
            models.Index(fields=["subject", "is_active"]),
        ]
        ordering = ["-id"]

    def __str__(self):
        return f"MCQ#{self.id} {self.title or self.question_text[:40]}"


class MCQOption(models.Model):
    question = models.ForeignKey(
        MCQQuestion, on_delete=models.CASCADE, related_name="options"
    )
    text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Option#{self.id} (Q{self.question_id})"


class MCQAttempt(models.Model):
    """Single-question practice attempt (moved here from the old mcq app)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mcq_attempts"
    )
    question = models.ForeignKey(MCQQuestion, on_delete=models.CASCADE, related_name="attempts")
    selected_option = models.ForeignKey(
        MCQOption, on_delete=models.PROTECT, related_name="attempts"
    )
    is_correct = models.BooleanField(default=False)
    attempt_no = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["user", "question"]),
            models.Index(fields=["question", "is_correct"]),
        ]

    def __str__(self):
        return f"Attempt#{self.id} U{self.user_id} Q{self.question_id} {'✓' if self.is_correct else '✗'}"


class PracticeQuestion(models.Model):
    prompt = models.TextField()

    answer_text = models.TextField(blank=True, default="")
    explanation = models.TextField(blank=True, default="")

    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="practice_questions",
    )
    chapter = models.ForeignKey(
        "academics.Chapter", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="practice_questions",
    )
    topic = models.ForeignKey(
        "academics.Topic", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="practice_questions",
    )

    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="practice_questions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["topic", "difficulty", "is_active"]),
        ]
        ordering = ["-id"]

    def __str__(self):
        return f"Practice#{self.id} {self.prompt[:40]}"


class ReportStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    REVIEWED = "REVIEWED", "Reviewed"
    RESOLVED = "RESOLVED", "Resolved"


class QuestionType(models.TextChoices):
    MCQ = "MCQ", "MCQ"
    PRACTICE = "PRACTICE", "Practice"


class QuestionReport(models.Model):
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)

    mcq_question = models.ForeignKey(
        MCQQuestion, on_delete=models.CASCADE, null=True, blank=True, related_name="reports"
    )
    practice_question = models.ForeignKey(
        PracticeQuestion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
    )

    reason = models.CharField(max_length=255)
    details = models.TextField(blank=True, default="")

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="question_reports",
    )
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Report#{self.id} {self.question_type} {self.status}"
