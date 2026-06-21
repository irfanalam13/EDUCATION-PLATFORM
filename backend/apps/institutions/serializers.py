from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Institution, InstitutionMember,
    Batch, BatchStaff, BatchInvite,
    Enrollment,
    CoursePack, CoursePackItem,
    Assignment, AssignmentItem,
    Submission, SubmissionAttempt,
    Grade, RegradeRequest,
    Rubric, RubricCriterion, RubricScore,
    Certificate, AuditLog,
    ParentLink,
)


# -------- Institution --------
class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ["id", "name", "slug", "domain", "require_approval_for_students", "is_active", "created_at"]


class InstitutionMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionMember
        fields = ["id", "institution", "user", "role", "status", "joined_at", "created_at"]


# -------- Batch / Staff / Invite --------
class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ["id", "institution", "name", "code", "course_pack", "is_active", "created_at"]


class BatchStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchStaff
        fields = ["id", "batch", "user", "role", "created_at"]


class BatchInviteCreateSerializer(serializers.Serializer):
    expires_in_hours = serializers.IntegerField(required=False, min_value=1, max_value=24*365)
    max_uses = serializers.IntegerField(required=False, min_value=0)

    def create(self, validated_data):
        batch: Batch = self.context["batch"]
        user = self.context["request"].user

        code = __import__("uuid").uuid4().hex[:10]
        expires_in = validated_data.get("expires_in_hours")
        expires_at = timezone.now() + timezone.timedelta(hours=expires_in) if expires_in else None
        max_uses = validated_data.get("max_uses", 0)

        return BatchInvite.objects.create(
            batch=batch,
            code=code,
            expires_at=expires_at,
            max_uses=max_uses,
            created_by=user,
        )


class BatchInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchInvite
        fields = ["id", "batch", "code", "expires_at", "max_uses", "used_count", "created_at"]


# -------- Enrollment --------
class JoinInstitutionSerializer(serializers.Serializer):
    invite_code = serializers.CharField()

    def validate(self, attrs):
        code = attrs["invite_code"].strip()
        invite = BatchInvite.objects.filter(code=code).select_related("batch", "batch__institution").first()
        if not invite or not invite.is_valid():
            raise serializers.ValidationError({"invite_code": "Invalid or expired invite code."})
        attrs["invite"] = invite
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        invite: BatchInvite = validated_data["invite"]
        batch = invite.batch
        inst = batch.institution

        # ensure membership exists
        InstitutionMember.objects.get_or_create(
            institution=inst,
            user=request.user,
            defaults={"role": InstitutionMember.Role.STUDENT, "status": InstitutionMember.Status.ACTIVE},
        )

        status = Enrollment.Status.PENDING if inst.require_approval_for_students else Enrollment.Status.APPROVED
        enrollment, created = Enrollment.objects.get_or_create(batch=batch, user=request.user, defaults={"status": status})

        if created:
            invite.used_count += 1
            invite.save(update_fields=["used_count"])

        return enrollment


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["id", "batch", "user", "status", "approved_by", "approved_at", "created_at"]


class EnrollmentApproveSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()
    approve = serializers.BooleanField(default=True)

    def validate(self, attrs):
        e = Enrollment.objects.select_related("batch", "batch__institution").filter(id=attrs["enrollment_id"]).first()
        if not e:
            raise serializers.ValidationError({"enrollment_id": "Not found."})
        attrs["enrollment"] = e
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        e: Enrollment = validated_data["enrollment"]

        if validated_data["approve"]:
            e.status = Enrollment.Status.APPROVED
            e.approved_by = request.user
            e.approved_at = timezone.now()
        else:
            e.status = Enrollment.Status.REJECTED
            e.approved_by = request.user
            e.approved_at = timezone.now()
        e.save()
        return e


# -------- Course Pack --------
class CoursePackItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoursePackItem
        fields = ["id", "course_pack", "order", "content_type", "object_id", "created_at"]


class CoursePackSerializer(serializers.ModelSerializer):
    items = CoursePackItemSerializer(many=True, read_only=True)

    class Meta:
        model = CoursePack
        fields = ["id", "institution", "title", "description", "is_published", "items", "created_at"]


# -------- Assignment / Items --------
class AssignmentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentItem
        fields = ["id", "assignment", "order", "prompt", "resource_url", "max_score", "created_at"]


class AssignmentSerializer(serializers.ModelSerializer):
    items = AssignmentItemSerializer(many=True, read_only=True)

    class Meta:
        model = Assignment
        fields = [
            "id", "batch", "title", "instructions",
            "type", "visibility",
            "start_at", "due_at",
            "late_policy", "late_penalty_percent",
            "max_attempts",
            "quiz_template_id", "practice_scope",
            "created_by",
            "items",
            "created_at",
        ]


class AssignmentCreateSerializer(serializers.ModelSerializer):
    items = AssignmentItemSerializer(many=True, required=False)

    class Meta:
        model = Assignment
        fields = [
            "batch", "title", "instructions",
            "type",
            "start_at", "due_at",
            "late_policy", "late_penalty_percent",
            "max_attempts",
            "quiz_template_id", "practice_scope",
            "items",
        ]

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        request = self.context["request"]
        assignment = Assignment.objects.create(created_by=request.user, **validated_data)
        for i in items:
            AssignmentItem.objects.create(assignment=assignment, **i)
        return assignment


# -------- Submission / Attempts --------
class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ["id", "assignment", "user", "text_answer", "file_url", "status", "submitted_at", "created_at"]


class SubmissionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionAttempt
        fields = ["id", "submission", "attempt_no", "started_at", "finished_at", "time_spent_seconds", "ip_hash", "device_hash", "created_at"]


class SubmitAssignmentSerializer(serializers.Serializer):
    text_answer = serializers.CharField(required=False, allow_blank=True)
    file_url = serializers.URLField(required=False, allow_blank=True)
    attempt_no = serializers.IntegerField(required=False, min_value=1)
    time_spent_seconds = serializers.IntegerField(required=False, min_value=0)
    ip_hash = serializers.CharField(required=False, allow_blank=True)
    device_hash = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        assignment: Assignment = self.context["assignment"]

        submission, _ = Submission.objects.get_or_create(
            assignment=assignment, user=request.user, defaults={
                "text_answer": validated_data.get("text_answer", ""),
                "file_url": validated_data.get("file_url", ""),
                "status": "SUBMITTED",
            }
        )

        # enforce attempts
        attempt_no = validated_data.get("attempt_no", 1)
        if attempt_no > assignment.max_attempts:
            raise serializers.ValidationError({"attempt_no": "Max attempts exceeded."})

        # update submission content
        submission.text_answer = validated_data.get("text_answer", submission.text_answer)
        submission.file_url = validated_data.get("file_url", submission.file_url)
        submission.submitted_at = timezone.now()
        submission.status = "SUBMITTED"
        submission.save()

        SubmissionAttempt.objects.update_or_create(
            submission=submission,
            attempt_no=attempt_no,
            defaults={
                "finished_at": timezone.now(),
                "time_spent_seconds": validated_data.get("time_spent_seconds", 0),
                "ip_hash": validated_data.get("ip_hash", ""),
                "device_hash": validated_data.get("device_hash", ""),
            }
        )

        return submission


# -------- Grade / Rubric / Regrade --------
class GradeSerializer(serializers.ModelSerializer):
    final_score = serializers.SerializerMethodField()

    class Meta:
        model = Grade
        fields = ["id", "submission", "score", "final_score", "feedback", "graded_by", "graded_at", "created_at"]

    def get_final_score(self, obj: Grade):
        return obj.apply_late_penalty()


class GradeCreateSerializer(serializers.Serializer):
    score = serializers.FloatField(min_value=0.0)
    feedback = serializers.CharField(required=False, allow_blank=True)

    def create(self, validated_data):
        request = self.context["request"]
        submission: Submission = self.context["submission"]
        grade, _ = Grade.objects.update_or_create(
            submission=submission,
            defaults={
                "score": validated_data["score"],
                "feedback": validated_data.get("feedback", ""),
                "graded_by": request.user,
                "graded_at": timezone.now(),
            }
        )
        submission.status = "GRADED"
        submission.save(update_fields=["status"])
        return grade


class RegradeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegradeRequest
        fields = ["id", "submission", "message", "status", "resolved_by", "resolved_at", "created_at"]


class RubricCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RubricCriterion
        fields = ["id", "rubric", "title", "description", "max_score", "created_at"]


class RubricSerializer(serializers.ModelSerializer):
    criteria = RubricCriterionSerializer(many=True, read_only=True)

    class Meta:
        model = Rubric
        fields = ["id", "assignment", "title", "criteria", "created_at"]


class RubricScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = RubricScore
        fields = ["id", "submission", "criterion", "score", "note", "created_at"]


# -------- Certificates --------
class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ["id", "batch", "user", "issued_at", "verify_code", "created_at"]


# -------- Parent link --------
class ParentLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentLink
        fields = ["id", "parent", "student", "institution", "created_at"]


# -------- Audit --------
class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "actor", "institution", "batch", "action", "object_type", "object_id", "meta", "created_at"]
