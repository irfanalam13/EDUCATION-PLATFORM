from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """
    Object must have .owner OR .user OR .created_by.
    Prefer standardizing models to use `owner`.
    """
    def has_object_permission(self, request, view, obj):
        u = request.user
        if not u or not u.is_authenticated:
            return False

        owner = (
            getattr(obj, "owner", None)
            or getattr(obj, "user", None)
            or getattr(obj, "created_by", None)
            or getattr(obj, "reporter", None)
        )
        return owner == u


class IsTeacherOrAdmin(BasePermission):
    """
    Assumes user has `role` OR `is_staff`.
    Update role names if your User model differs.
    """
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u
            and u.is_authenticated
            and (getattr(u, "is_staff", False) or getattr(u, "role", "") in ["teacher", "admin"])
        )


class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return bool(u and u.is_authenticated and getattr(u, "is_staff", False))


class IsTeacherInBatch(BasePermission):
    """
    Requires:
      - obj.batch.teachers (ManyToMany users) OR
      - view.get_batch() -> returns batch with .teachers
    Adapt if you use CohortMember-type join table.
    """
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False

        get_batch = getattr(view, "get_batch", None)
        if callable(get_batch):
            batch = get_batch()
            return bool(batch and batch.teachers.filter(id=u.id).exists())

        return True  # fallback to object-level

    def has_object_permission(self, request, view, obj):
        u = request.user
        batch = getattr(obj, "batch", None)
        return bool(batch and batch.teachers.filter(id=u.id).exists())


class IsStudentInBatch(BasePermission):
    def has_object_permission(self, request, view, obj):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        batch = getattr(obj, "batch", None)
        return bool(batch and batch.students.filter(id=u.id).exists())


class IsEnrolledInInstitution(BasePermission):
    """
    Requires:
      - obj.institution.members (ManyToMany users) OR
      - view.get_institution() -> returns institution with .members
    Adapt if you use a membership join model.
    """
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False

        get_inst = getattr(view, "get_institution", None)
        if callable(get_inst):
            inst = get_inst()
            return bool(inst and inst.members.filter(id=u.id).exists())

        return True  # fallback to object-level

    def has_object_permission(self, request, view, obj):
        u = request.user
        inst = getattr(obj, "institution", None)
        if not inst:
            return True
        return inst.members.filter(id=u.id).exists()
