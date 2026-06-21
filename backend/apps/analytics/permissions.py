"""RBAC for analytics. Institution admins see everything for their institution;
teachers see their own teaching analytics; students/parents see that student."""
from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.institutions.models import BatchStaff, Enrollment, ParentLink
from apps.institutions.permissions import _is_inst_admin


def _q_int(request, *keys):
    for k in keys:
        val = request.query_params.get(k) or request.data.get(k)
        if val:
            try:
                return int(val)
            except (TypeError, ValueError):
                return None
    return None


def _is_teacher_in_institution(user, institution_id: int) -> bool:
    return BatchStaff.objects.filter(user=user, batch__institution_id=institution_id).exists()


def _teaches_student(user, institution_id: int, student_id: int) -> bool:
    batch_ids = BatchStaff.objects.filter(
        user=user, batch__institution_id=institution_id
    ).values_list("batch_id", flat=True)
    return Enrollment.objects.filter(
        batch_id__in=batch_ids, user_id=student_id, status=Enrollment.Status.APPROVED
    ).exists()


class IsInstitutionAdmin(BasePermission):
    """Institution admin, with institution_id taken from query or body."""

    message = "You must be an admin of this institution."

    def has_permission(self, request, view):
        inst = _q_int(request, "institution_id", "institution")
        if not inst or not request.user.is_authenticated:
            return False
        return _is_inst_admin(request.user, inst)


class CanViewTeacherAnalytics(BasePermission):
    """Institution admin (any teacher) or a teacher viewing their own analytics."""

    message = "Not allowed to view this teacher's analytics."

    def has_permission(self, request, view):
        user = request.user
        inst = _q_int(request, "institution_id", "institution")
        if not user.is_authenticated or not inst:
            return False
        if _is_inst_admin(user, inst):
            return True
        teacher_id = _q_int(request, "teacher_id")
        if teacher_id and teacher_id != user.id:
            return False  # non-admins may only see themselves
        return _is_teacher_in_institution(user, inst)


class CanViewStudentAnalytics(BasePermission):
    """Self, an institution admin, a teacher of the student, or a linked parent."""

    message = "Not allowed to view this student's analytics."

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        student_id = _q_int(request, "student_id", "student")
        if not student_id:
            return False
        if student_id == user.id:
            return True
        inst = _q_int(request, "institution_id", "institution")
        if not inst:
            return False
        if _is_inst_admin(user, inst):
            return True
        if _teaches_student(user, inst, student_id):
            return True
        return ParentLink.objects.filter(
            parent=user, student_id=student_id, institution_id=inst
        ).exists()
