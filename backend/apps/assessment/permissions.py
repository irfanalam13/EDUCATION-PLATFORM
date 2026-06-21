from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsTeacherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


class IsOwnerOfSession(BasePermission):
    """
    For QuizSessionViewSet object-level permission.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user and user.is_authenticated and obj.user_id == user.id)
