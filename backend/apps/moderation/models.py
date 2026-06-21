from django.conf import settings
from django.db import models


class Report(models.Model):
    class TargetType(models.TextChoices):
        CONTENT = "content", "Content"
        QUESTION = "question", "Question"
        COMMENT = "comment", "Comment"
        USER = "user", "User"
        INSTITUTION = "institution", "Institution"
        OTHER = "other", "Other"

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        ABUSE = "abuse", "Abuse / Harassment"
        CHEATING = "cheating", "Cheating"
        COPYRIGHT = "copyright", "Copyright"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWING = "reviewing", "Reviewing"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_made",
    )

    # Generic reference (safe dependency: does not FK other apps)
    target_type = models.CharField(max_length=32, choices=TargetType.choices)
    target_id = models.CharField(max_length=64)  # store UUID/int as string

    reason = models.CharField(max_length=32, choices=Reason.choices)
    message = models.TextField(blank=True)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_resolved",
    )
    resolved_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["reason"]),
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Report({self.id}) {self.target_type}:{self.target_id} [{self.status}]"


class ContentFlag(models.Model):
    class FlagType(models.TextChoices):
        NSFW = "nsfw", "NSFW"
        DUPLICATE = "duplicate", "Duplicate"
        POLICY = "policy", "Policy violation"
        LOW_QUALITY = "low_quality", "Low quality"
        COPYRIGHT = "copyright", "Copyright"

    # Generic reference (does not FK other apps)
    target_type = models.CharField(max_length=32)
    target_id = models.CharField(max_length=64)

    flag_type = models.CharField(max_length=32, choices=FlagType.choices)
    severity = models.PositiveSmallIntegerField(default=1)  # 1..5
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flags_created",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["flag_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self):
        return f"Flag({self.id}) {self.flag_type} {self.target_type}:{self.target_id}"
