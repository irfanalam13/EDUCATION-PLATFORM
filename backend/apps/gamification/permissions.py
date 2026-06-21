# apps/gamification/permissions.py
from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = getattr(obj, "user", None)
        return user == request.user

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
