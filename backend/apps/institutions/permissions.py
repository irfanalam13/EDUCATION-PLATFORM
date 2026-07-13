from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import (
    InstitutionMember, BatchStaff, Enrollment, ParentLink
)

def _is_inst_admin(user, institution_id: int) -> bool:
    return InstitutionMember.objects.filter(
        institution_id=institution_id, user=user, role=InstitutionMember.Role.ADMIN,
        status=InstitutionMember.Status.ACTIVE
    ).exists()

def _is_batch_staff(user, batch_id: int) -> bool:
    return BatchStaff.objects.filter(batch_id=batch_id, user=user).exists()

def _is_batch_owner(user, batch_id: int) -> bool:
    return BatchStaff.objects.filter(batch_id=batch_id, user=user, role=BatchStaff.Role.OWNER).exists()

def _is_teacher_or_ta(user, batch_id: int) -> bool:
    return BatchStaff.objects.filter(
        batch_id=batch_id, user=user,
        role__in=[BatchStaff.Role.OWNER, BatchStaff.Role.TEACHER, BatchStaff.Role.TA]
    ).exists()

def _is_student_approved(user, batch_id: int) -> bool:
    return Enrollment.objects.filter(batch_id=batch_id, user=user, status=Enrollment.Status.APPROVED).exists()

def _is_parent_of(user, student_id: int, institution_id: int) -> bool:
    return ParentLink.objects.filter(parent=user, student_id=student_id, institution_id=institution_id).exists()


class IsInstitutionAdmin(BasePermission):
    def has_permission(self, request, view):
        inst_id = view.kwargs.get("institution_id") or request.data.get("institution") or request.query_params.get("institution_id")
        if not inst_id:
            return False
        return request.user.is_authenticated and _is_inst_admin(request.user, int(inst_id))


class IsBatchOwner(BasePermission):
    def has_permission(self, request, view):
        batch_id = view.kwargs.get("batch_id") or view.kwargs.get("pk") or request.data.get("batch") or request.query_params.get("batch_id")
        if not batch_id:
            return False
        return request.user.is_authenticated and _is_batch_owner(request.user, int(batch_id))


class IsBatchTeacherOrTA(BasePermission):
    def has_permission(self, request, view):
        batch_id = view.kwargs.get("batch_id") or view.kwargs.get("pk") or request.data.get("batch") or request.query_params.get("batch_id")
        if not batch_id:
            return False
        return request.user.is_authenticated and _is_teacher_or_ta(request.user, int(batch_id))


class IsStudentApprovedInBatch(BasePermission):
    def has_permission(self, request, view):
        batch_id = view.kwargs.get("batch_id") or view.kwargs.get("pk") or request.data.get("batch") or request.query_params.get("batch_id")
        if not batch_id:
            return False
        return request.user.is_authenticated and _is_student_approved(request.user, int(batch_id))


def _resolve_batch_id(obj):
    """Find the batch id for an object that is (or belongs to) a batch.

    Works for Assignment (obj.batch_id) and Submission (obj.assignment.batch_id).
    """
    if getattr(obj, "batch_id", None):
        return obj.batch_id
    assignment = getattr(obj, "assignment", None)
    if assignment is not None:
        return getattr(assignment, "batch_id", None)
    return None


class IsBatchStaffForObject(BasePermission):
    """Object-level: writes require teacher/TA/owner of the OBJECT's batch.

    This is the correct replacement for the broken view-level checks that read
    batch_id from `pk` (which is the assignment/submission id on detail routes).
    Reads are allowed (querysets already scope visibility).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        batch_id = _resolve_batch_id(obj)
        return batch_id is not None and _is_teacher_or_ta(request.user, int(batch_id))


class IsParentOfStudent(BasePermission):
    """
    For endpoints like /students/{id}/report/ where parent can view their child's report
    """
    def has_permission(self, request, view):
        student_id = view.kwargs.get("student_id") or view.kwargs.get("pk")
        institution_id = request.query_params.get("institution_id") or request.data.get("institution_id")
        if not (student_id and institution_id):
            return False
        return request.user.is_authenticated and _is_parent_of(request.user, int(student_id), int(institution_id))
