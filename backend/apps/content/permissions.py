from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadByVisibility(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            visibility = getattr(obj, "visibility", None)
            if visibility in ("public", "unlisted"):
                return True
            return request.user.is_authenticated and getattr(obj, "created_by_id", None) == request.user.id
        return request.user.is_authenticated and getattr(obj, "created_by_id", None) == request.user.id


class IsUploaderOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and getattr(obj, "uploaded_by_id", None) == request.user.id


class IsCreatorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner_id = getattr(obj, "created_by_id", None) or getattr(obj, "user_id", None)
        return request.user.is_authenticated and owner_id == request.user.id


class IsNoteOwnerOrReadOnly(BasePermission):
    """Write access to a NoteTag is limited to the owner of the parent note."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        note = getattr(obj, "note", None)
        return (
            request.user.is_authenticated
            and note is not None
            and getattr(note, "created_by_id", None) == request.user.id
        )


class IsCollectionOwnerOrReadOnly(BasePermission):
    """Write access to a CollectionItem is limited to the collection's owner."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        collection = getattr(obj, "collection", None)
        return (
            request.user.is_authenticated
            and collection is not None
            and getattr(collection, "created_by_id", None) == request.user.id
        )
