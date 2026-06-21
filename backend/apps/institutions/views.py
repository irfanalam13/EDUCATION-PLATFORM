from __future__ import annotations

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Institution, InstitutionMember,
    Batch, BatchStaff, BatchInvite,
    Enrollment,
    CoursePack, CoursePackItem,
    Assignment, Submission, Grade,
    Certificate, AuditLog,
    ParentLink,
)
from .permissions import (
    IsInstitutionAdmin, IsBatchOwner, IsBatchTeacherOrTA, IsStudentApprovedInBatch,
    IsParentOfStudent, IsBatchStaffForObject,
    _is_teacher_or_ta, _is_inst_admin,
)
from .serializers import (
    InstitutionSerializer, InstitutionMemberSerializer,
    BatchSerializer, BatchStaffSerializer, BatchInviteCreateSerializer, BatchInviteSerializer,
    JoinInstitutionSerializer, EnrollmentSerializer, EnrollmentApproveSerializer,
    CoursePackSerializer, CoursePackItemSerializer,
    AssignmentSerializer, AssignmentCreateSerializer,
    SubmissionSerializer, SubmitAssignmentSerializer,
    GradeSerializer, GradeCreateSerializer,
    RegradeRequestSerializer,
    CertificateSerializer,
    ParentLinkSerializer,
    AuditLogSerializer,
)


def log_action(actor, institution=None, batch=None, action="", obj=None, meta=None):
    if obj is None:
        return
    AuditLog.objects.create(
        actor=actor,
        institution=institution,
        batch=batch,
        action=action,
        object_type=obj.__class__.__name__,
        object_id=str(getattr(obj, "id", "")),
        meta=meta or {},
    )


# ---------------- Institution ----------------
class InstitutionViewSet(viewsets.ModelViewSet):
    serializer_class = InstitutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only institutions where user is a member
        return Institution.objects.filter(members__user=self.request.user).distinct()

    def perform_create(self, serializer):
        inst = serializer.save()
        # creator becomes InstitutionAdmin
        InstitutionMember.objects.get_or_create(
            institution=inst,
            user=self.request.user,
            defaults={"role": InstitutionMember.Role.ADMIN, "status": InstitutionMember.Status.ACTIVE},
        )
        log_action(self.request.user, institution=inst, action="INSTITUTION_CREATED", obj=inst)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        memberships = InstitutionMember.objects.filter(user=request.user).select_related("institution")
        insts = [m.institution for m in memberships]
        return Response(InstitutionSerializer(insts, many=True).data)


class InstitutionMemberViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InstitutionMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        inst_id = self.request.query_params.get("institution_id")
        qs = InstitutionMember.objects.select_related("institution").filter(user=self.request.user)
        if inst_id:
            qs = qs.filter(institution_id=inst_id)
        return qs


# ---------------- Batch ----------------
class BatchViewSet(viewsets.ModelViewSet):
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # user can see batches where they are enrolled OR staff OR institution member
        user = self.request.user
        return Batch.objects.filter(
            Q(enrollments__user=user) |
            Q(staff__user=user) |
            Q(institution__members__user=user)
        ).distinct().select_related("institution")

    def perform_create(self, serializer):
        batch = serializer.save()
        # creator becomes OWNER
        BatchStaff.objects.get_or_create(batch=batch, user=self.request.user, defaults={"role": BatchStaff.Role.OWNER})
        log_action(self.request.user, institution=batch.institution, batch=batch, action="BATCH_CREATED", obj=batch)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsBatchTeacherOrTA], url_path="invite")
    def invite(self, request, pk=None):
        batch = self.get_object()
        ser = BatchInviteCreateSerializer(data=request.data, context={"batch": batch, "request": request})
        ser.is_valid(raise_exception=True)
        invite = ser.save()
        log_action(request.user, institution=batch.institution, batch=batch, action="BATCH_INVITE_CREATED", obj=invite)
        return Response(BatchInviteSerializer(invite).data, status=201)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated], url_path="leaderboard")
    def leaderboard(self, request, pk=None):
        """
        Leaderboard metrics:
        - score: sum of final grade scores
        - submissions: number of submissions
        """
        batch = self.get_object()
        metric = request.query_params.get("metric", "score")
        period = request.query_params.get("period", "all")  # weekly/monthly/all

        now = timezone.now()
        start = None
        if period == "weekly":
            start = now - timezone.timedelta(days=7)
        elif period == "monthly":
            start = now - timezone.timedelta(days=30)

        subs = Submission.objects.filter(assignment__batch=batch)
        if start:
            subs = subs.filter(submitted_at__gte=start)

        if metric == "submissions":
            rows = subs.values("user").annotate(value=Count("id")).order_by("-value")[:50]
        else:
            # score (sum of final score). Use Grade.score (late penalty can be applied on client or recomputed later).
            rows = Grade.objects.filter(submission__in=subs).values("submission__user").annotate(value=Sum("score")).order_by("-value")[:50]
            rows = [{"user": r["submission__user"], "value": r["value"] or 0} for r in rows]

        return Response({"batch_id": batch.id, "metric": metric, "period": period, "rows": rows})

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated, IsBatchTeacherOrTA], url_path="analytics")
    def analytics(self, request, pk=None):
        batch = self.get_object()
        total_students = Enrollment.objects.filter(batch=batch, status=Enrollment.Status.APPROVED).count()
        total_assignments = batch.assignments.filter(visibility=Assignment.Visibility.PUBLISHED).count()
        total_submissions = Submission.objects.filter(assignment__batch=batch).count()
        avg_score = Grade.objects.filter(submission__assignment__batch=batch).aggregate(avg=Avg("score"))["avg"] or 0

        return Response({
            "batch_id": batch.id,
            "students": total_students,
            "assignments": total_assignments,
            "submissions": total_submissions,
            "avg_score": avg_score,
        })


# ---------------- Enrollment / Join ----------------
class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).select_related("batch", "batch__institution")

    @action(detail=False, methods=["post"], url_path="join", permission_classes=[IsAuthenticated])
    def join(self, request):
        ser = JoinInstitutionSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        enrollment = ser.save()
        log_action(request.user, institution=enrollment.batch.institution, batch=enrollment.batch, action="ENROLLMENT_CREATED", obj=enrollment)
        return Response(EnrollmentSerializer(enrollment).data, status=201)

    @action(detail=False, methods=["post"], url_path="approve", permission_classes=[IsAuthenticated])
    def approve(self, request):
        ser = EnrollmentApproveSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        # Authorize against the ENROLLMENT's real batch (not a client-supplied
        # `batch`), so a teacher can't approve enrollments in batches they don't own.
        enrollment_obj = ser.validated_data["enrollment"]
        if not _is_teacher_or_ta(request.user, enrollment_obj.batch_id):
            raise PermissionDenied("You can only approve enrollments for batches you teach.")
        enrollment = ser.save()
        log_action(request.user, institution=enrollment.batch.institution, batch=enrollment.batch, action="ENROLLMENT_APPROVED_UPDATED", obj=enrollment, meta={"status": enrollment.status})
        return Response(EnrollmentSerializer(enrollment).data)


# ---------------- Course Packs ----------------
class CoursePackViewSet(viewsets.ModelViewSet):
    serializer_class = CoursePackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CoursePack.objects.filter(institution__members__user=self.request.user).distinct()

    def perform_create(self, serializer):
        cp = serializer.save()
        log_action(self.request.user, institution=cp.institution, action="COURSEPACK_CREATED", obj=cp)


class CoursePackItemViewSet(viewsets.ModelViewSet):
    serializer_class = CoursePackItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CoursePackItem.objects.filter(course_pack__institution__members__user=self.request.user).distinct()


# ---------------- Assignments ----------------
class AssignmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Assignment.objects.filter(batch__institution__members__user=self.request.user).distinct()
        batch_id = self.request.query_params.get("batch_id")
        if batch_id:
            qs = qs.filter(batch_id=batch_id)
        # students should only see published
        # teacher/TA can see drafts too (handled lightly here)
        if not BatchStaff.objects.filter(user=self.request.user, batch_id__in=qs.values("batch_id")).exists():
            qs = qs.filter(visibility=Assignment.Visibility.PUBLISHED)
        return qs.select_related("batch", "batch__institution")

    def get_serializer_class(self):
        if self.action in ["create"]:
            return AssignmentCreateSerializer
        return AssignmentSerializer

    def get_permissions(self):
        # create resolves batch from request.data["batch"] (correct);
        # detail writes use object-level check against the assignment's own batch.
        if self.action == "create":
            return [IsAuthenticated(), IsBatchTeacherOrTA()]
        if self.action in ["update", "partial_update", "destroy", "publish"]:
            return [IsAuthenticated(), IsBatchStaffForObject()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        a = serializer.save()
        log_action(self.request.user, institution=a.batch.institution, batch=a.batch, action="ASSIGNMENT_CREATED", obj=a)

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        a = self.get_object()  # enforces IsBatchStaffForObject for this batch
        a.visibility = Assignment.Visibility.PUBLISHED
        a.save(update_fields=["visibility"])
        log_action(request.user, institution=a.batch.institution, batch=a.batch, action="ASSIGNMENT_PUBLISHED", obj=a)
        return Response(AssignmentSerializer(a).data)


# ---------------- Submissions ----------------
class SubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Student sees only their own submissions; staff see submissions ONLY for
        # batches they actually staff (previously any staff member saw every
        # submission across all institutions).
        user = self.request.user
        staff_batch_ids = list(
            BatchStaff.objects.filter(user=user).values_list("batch_id", flat=True)
        )
        qs = (
            Submission.objects
            .filter(Q(user=user) | Q(assignment__batch_id__in=staff_batch_ids))
            .select_related("assignment", "assignment__batch")
            .distinct()
        )
        return qs

    @action(detail=False, methods=["post"], url_path=r"assignments/(?P<assignment_id>\d+)/submit",
            permission_classes=[IsAuthenticated, IsStudentApprovedInBatch])
    def submit(self, request, assignment_id=None):
        assignment = Assignment.objects.select_related("batch", "batch__institution").filter(id=assignment_id).first()
        if not assignment:
            return Response({"detail": "Assignment not found."}, status=404)

        # verify student approved in this batch
        if not Enrollment.objects.filter(batch=assignment.batch, user=request.user, status=Enrollment.Status.APPROVED).exists():
            return Response({"detail": "Not approved in this batch."}, status=403)

        ser = SubmitAssignmentSerializer(data=request.data, context={"request": request, "assignment": assignment})
        ser.is_valid(raise_exception=True)
        submission = ser.save()
        log_action(request.user, institution=assignment.batch.institution, batch=assignment.batch, action="SUBMISSION_CREATED", obj=submission)
        return Response(SubmissionSerializer(submission).data, status=201)

    @action(detail=True, methods=["post"], url_path="grade", permission_classes=[IsAuthenticated, IsBatchStaffForObject])
    def grade(self, request, pk=None):
        # IsBatchStaffForObject (via get_object) verifies the grader is a
        # teacher/TA of THIS submission's batch — fixes grade tampering where the
        # old check read batch_id from the submission's pk.
        submission = self.get_object()
        ser = GradeCreateSerializer(data=request.data, context={"request": request, "submission": submission})
        ser.is_valid(raise_exception=True)
        grade = ser.save()
        log_action(request.user, institution=submission.assignment.batch.institution, batch=submission.assignment.batch, action="GRADE_UPDATED", obj=grade)
        return Response(GradeSerializer(grade).data)

    @action(detail=True, methods=["post"], url_path="regrade-request", permission_classes=[IsAuthenticated])
    def regrade_request(self, request, pk=None):
        submission = self.get_object()
        if submission.user != request.user:
            return Response({"detail": "You can request regrade only for your submission."}, status=403)

        msg = request.data.get("message", "").strip()
        if not msg:
            return Response({"message": "Required."}, status=400)

        rr = submission.regrade_requests.create(message=msg)
        log_action(request.user, institution=submission.assignment.batch.institution, batch=submission.assignment.batch, action="REGRADE_REQUEST_CREATED", obj=rr)
        return Response(RegradeRequestSerializer(rr).data, status=201)


# ---------------- Certificates ----------------
class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"], url_path=r"verify/(?P<code>[a-f0-9]{32})", permission_classes=[IsAuthenticated])
    def verify(self, request, code=None):
        c = Certificate.objects.filter(verify_code=code).select_related("batch", "batch__institution").first()
        if not c:
            return Response({"detail": "Invalid certificate code."}, status=404)
        return Response(CertificateSerializer(c).data)


# ---------------- Parent ----------------
class ParentLinkViewSet(viewsets.ModelViewSet):
    serializer_class = ParentLinkSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # A parent sees their own links; an institution admin sees their org's links.
        user = self.request.user
        admin_inst_ids = InstitutionMember.objects.filter(
            user=user, role=InstitutionMember.Role.ADMIN,
            status=InstitutionMember.Status.ACTIVE,
        ).values_list("institution_id", flat=True)
        return ParentLink.objects.filter(
            Q(parent=user) | Q(institution_id__in=admin_inst_ids)
        ).distinct()

    def perform_create(self, serializer):
        # Parent-student links are an administrative action: only an admin of the
        # target institution may create them (prevents linking yourself as parent
        # of an arbitrary student).
        institution = serializer.validated_data.get("institution")
        if institution is None or not _is_inst_admin(self.request.user, institution.id):
            raise PermissionDenied("Only an institution admin can create parent links.")
        serializer.save()


# ---------------- Audit log ----------------
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AuditLog.objects.filter(
            Q(institution__members__user=self.request.user) | Q(actor=self.request.user)
        ).distinct().order_by("-created_at")
