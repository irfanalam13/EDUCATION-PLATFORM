from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.institutions.models import Institution

User = settings.AUTH_USER_MODEL


class InstitutionDailySnapshot(models.Model):
    """One row per institution per day of pre-computed headline metrics.

    Live dashboards compute on-read; this table persists a daily time-series so
    trend/cohort charts and period reports keep history even after raw
    DailyActivity rows age out. Populated by the `snapshot_institutions` task.
    """

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="daily_snapshots"
    )
    date = models.DateField(db_index=True)

    active_students = models.PositiveIntegerField(default=0)
    daily_active_users = models.PositiveIntegerField(default=0)
    learning_minutes = models.PositiveIntegerField(default=0)
    avg_quiz_score = models.FloatField(default=0.0)
    assignment_completion_rate = models.FloatField(default=0.0)
    avg_mastery = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "date"], name="uniq_inst_snapshot_per_day"
            )
        ]
        indexes = [models.Index(fields=["institution", "date"])]
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.institution_id}@{self.date}"


class AnalyticsReport(models.Model):
    """A generated PDF/Excel analytics report kept for download/history."""

    class Scope(models.TextChoices):
        INSTITUTION = "INSTITUTION", "Institution"
        TEACHER = "TEACHER", "Teacher"
        SUBJECT = "SUBJECT", "Subject"

    class Period(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        SEMESTER = "SEMESTER", "Semester"
        CUSTOM = "CUSTOM", "Custom"

    class Format(models.TextChoices):
        PDF = "PDF", "PDF"
        XLSX = "XLSX", "Excel"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        READY = "READY", "Ready"
        FAILED = "FAILED", "Failed"

    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name="analytics_reports"
    )
    scope = models.CharField(max_length=16, choices=Scope.choices, default=Scope.INSTITUTION)
    period = models.CharField(max_length=16, choices=Period.choices, default=Period.MONTHLY)
    file_format = models.CharField(max_length=8, choices=Format.choices, default=Format.PDF)

    title = models.CharField(max_length=255, blank=True, default="")
    period_start = models.DateField()
    period_end = models.DateField()

    file = models.FileField(upload_to="analytics_reports/", blank=True, null=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.READY)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="analytics_reports"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["institution", "created_at"])]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_scope_display()} report {self.institution_id} {self.period_start}..{self.period_end}"
