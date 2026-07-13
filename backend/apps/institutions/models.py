from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


User = settings.AUTH_USER_MODEL


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# -------------------------
# 1) Institution + Members
# -------------------------
class Institution(TimeStampedModel):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    # Optional: domain join
    domain = models.CharField(max_length=255, blank=True, default="")  # e.g. "college.edu"
    require_approval_for_students = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class InstitutionMember(TimeStampedModel):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        TEACHER = "TEACHER", "Teacher"
        TA = "TA", "Teacher Assistant"
        STUDENT = "STUDENT", "Student"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        PENDING = "PENDING", "Pending"
        SUSPENDED = "SUSPENDED", "Suspended"

    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="institution_memberships")
    role = models.CharField(max_length=16, choices=Role.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)

    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("institution", "user")]
        indexes = [
            models.Index(fields=["institution", "role"]),
            models.Index(fields=["institution", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.institution_id}:{self.user_id}:{self.role}"


# -------------------------
# 2) Batches + Staff
# -------------------------
class Batch(TimeStampedModel):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="batches")
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32, db_index=True, blank=True, default="")  # optional display code

    # CoursePack / syllabus
    course_pack = models.ForeignKey(
        "CoursePack", on_delete=models.SET_NULL, null=True, blank=True, related_name="batches"
    )

    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.institution.name})"


class BatchStaff(TimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        TEACHER = "TEACHER", "Teacher"
        TA = "TA", "Teacher Assistant"

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="staff")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="batch_staff_roles")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.TEACHER)

    class Meta:
        unique_together = [("batch", "user")]
        indexes = [
            models.Index(fields=["batch", "role"]),
        ]


# -------------------------
# 3) Enrollment + approvals
# -------------------------
class BatchInvite(TimeStampedModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="invites")
    code = models.CharField(max_length=32, unique=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(default=0)  # 0 means unlimited
    used_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def is_valid(self) -> bool:
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="enrollments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_enrollments")
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("batch", "user")]
        indexes = [
            models.Index(fields=["batch", "status"]),
            models.Index(fields=["user", "status"]),
        ]


# -------------------------
# 11) Course Packs / syllabus
# -------------------------
class CoursePack(TimeStampedModel):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="course_packs")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_published = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title


class CoursePackItem(TimeStampedModel):
    course_pack = models.ForeignKey(CoursePack, on_delete=models.CASCADE, related_name="items")
    order = models.PositiveIntegerField(default=0)

    # Generic links to other content (lesson, quiz template, pdf, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(fields=["course_pack", "order"]),
        ]
        ordering = ["order", "created_at"]


# -------------------------
# 3) Assignment types
# -------------------------
class Assignment(TimeStampedModel):
    class Type(models.TextChoices):
        HOMEWORK = "HOMEWORK", "Homework"
        QUIZ = "QUIZ", "Quiz"
        PRACTICE_SET = "PRACTICE_SET", "Practice Set"
        PROJECT = "PROJECT", "Project"

    class Visibility(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"

    class LatePolicy(models.TextChoices):
        NOT_ALLOWED = "NOT_ALLOWED", "No Late Submissions"
        ALLOW_WITH_PENALTY = "ALLOW_WITH_PENALTY", "Allow with Penalty"
        ALLOW_NO_PENALTY = "ALLOW_NO_PENALTY", "Allow without Penalty"

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=255)
    instructions = models.TextField(blank=True, default="")

    type = models.CharField(max_length=16, choices=Type.choices, default=Type.HOMEWORK)
    visibility = models.CharField(max_length=16, choices=Visibility.choices, default=Visibility.DRAFT)

    start_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)

    late_policy = models.CharField(max_length=24, choices=LatePolicy.choices, default=LatePolicy.NOT_ALLOWED)
    late_penalty_percent = models.PositiveIntegerField(default=0)  # used only for ALLOW_WITH_PENALTY

    max_attempts = models.PositiveIntegerField(default=1)

    # Integration hooks
    quiz_template_id = models.CharField(max_length=64, blank=True, default="")  # if type=QUIZ (points to assessments app)
    practice_scope = models.JSONField(blank=True, default=dict)  # if PRACTICE_SET

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_assignments")

    class Meta:
        indexes = [
            models.Index(fields=["batch", "visibility"]),
            models.Index(fields=["batch", "due_at"]),
        ]

    def clean(self):
        if self.late_policy == self.LatePolicy.ALLOW_WITH_PENALTY and self.late_penalty_percent <= 0:
            raise ValidationError("late_penalty_percent must be > 0 for ALLOW_WITH_PENALTY.")


class AssignmentItem(TimeStampedModel):
    """
    Items for HOMEWORK/PROJECT: prompts, required files, resources, etc.
    For QUIZ/PRACTICE_SET, you may keep items empty and use the integration fields.
    """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="items")
    order = models.PositiveIntegerField(default=0)

    prompt = models.TextField(blank=True, default="")
    resource_url = models.URLField(blank=True, default="")
    max_score = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]
        indexes = [models.Index(fields=["assignment", "order"])]


# -------------------------
# 4) Submission + attempts
# -------------------------
class Submission(TimeStampedModel):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")

    text_answer = models.TextField(blank=True, default="")
    file_url = models.URLField(blank=True, default="")  # store S3 URL if you use uploads
    status = models.CharField(max_length=16, default="SUBMITTED")  # SUBMITTED / GRADED / RETURNED

    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["assignment", "user"]),
            models.Index(fields=["assignment", "submitted_at"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["assignment", "user"], name="uniq_submission_per_user_per_assignment")
        ]


class SubmissionAttempt(TimeStampedModel):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="attempts")
    attempt_no = models.PositiveIntegerField(default=1)

    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)

    # integrity (store hashes, not raw IP/device)
    ip_hash = models.CharField(max_length=128, blank=True, default="")
    device_hash = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        unique_together = [("submission", "attempt_no")]
        indexes = [models.Index(fields=["submission", "attempt_no"])]


# -------------------------
# 4) Grade + regrade
# -------------------------
class Grade(TimeStampedModel):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name="grade")
    score = models.FloatField(default=0.0)
    feedback = models.TextField(blank=True, default="")
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="grades_given")
    graded_at = models.DateTimeField(default=timezone.now)

    def apply_late_penalty(self):
        a = self.submission.assignment
        if not a.due_at:
            return self.score
        if self.submission.submitted_at <= a.due_at:
            return self.score
        if a.late_policy == Assignment.LatePolicy.NOT_ALLOWED:
            return 0.0
        if a.late_policy == Assignment.LatePolicy.ALLOW_NO_PENALTY:
            return self.score
        if a.late_policy == Assignment.LatePolicy.ALLOW_WITH_PENALTY:
            penalty = (a.late_penalty_percent / 100.0) * self.score
            return max(0.0, self.score - penalty)
        return self.score


class RegradeRequest(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CLOSED = "CLOSED", "Closed"

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="regrade_requests")
    message = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)

    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="regrade_resolved")
    resolved_at = models.DateTimeField(null=True, blank=True)


# -------------------------
# 5) Rubrics
# -------------------------
class Rubric(TimeStampedModel):
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name="rubric")
    title = models.CharField(max_length=255, default="Rubric")


class RubricCriterion(TimeStampedModel):
    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE, related_name="criteria")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    max_score = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["created_at"]


class RubricScore(TimeStampedModel):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="rubric_scores")
    criterion = models.ForeignKey(RubricCriterion, on_delete=models.CASCADE, related_name="scores")
    score = models.FloatField(default=0.0)
    note = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("submission", "criterion")]


# -------------------------
# 10) Certificates
# -------------------------
class Certificate(TimeStampedModel):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="certificates")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates")

    issued_at = models.DateTimeField(default=timezone.now)
    verify_code = models.CharField(max_length=32, unique=True, db_index=True, default="")

    def save(self, *args, **kwargs):
        if not self.verify_code:
            self.verify_code = uuid.uuid4().hex[:32]
        super().save(*args, **kwargs)


# -------------------------
# 6) Audit Logs
# -------------------------
class AuditLog(TimeStampedModel):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)

    action = models.CharField(max_length=64)  # e.g. "ASSIGNMENT_CREATED", "GRADE_UPDATED"
    object_type = models.CharField(max_length=64)  # e.g. "Assignment"
    object_id = models.CharField(max_length=64)
    meta = models.JSONField(blank=True, default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["institution", "created_at"]),
            models.Index(fields=["batch", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]


# -------------------------
# 12) Parent link (Nepal-friendly)
# -------------------------
class ParentLink(TimeStampedModel):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parent_links")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_parents")
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="parent_links")

    class Meta:
        unique_together = [("parent", "student", "institution")]
        indexes = [models.Index(fields=["institution", "student"])]
