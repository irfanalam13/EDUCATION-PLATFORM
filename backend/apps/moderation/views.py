from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied

from django_filters.rest_framework import DjangoFilterBackend

from .models import Report
from .serializers import (
    ReportCreateSerializer,
    ReportReadSerializer,
    ReportAdminUpdateSerializer,
)
from .filters import ReportFilter


class ReportViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    POST   /api/moderation/reports/        -> any authenticated user
    GET    /api/moderation/reports/        -> admin only (list all)
    GET    /api/moderation/reports/{id}/   -> admin only
    PATCH  /api/moderation/reports/{id}/   -> admin only (status updates)
    """
    queryset = Report.objects.select_related("reporter", "resolved_by").all()

    filter_backends = [DjangoFilterBackend]
    filterset_class = ReportFilter

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        # admin-only for everything else
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return ReportCreateSerializer
        if self.action in ["partial_update", "update"]:
            return ReportAdminUpdateSerializer
        return ReportReadSerializer

    def list(self, request, *args, **kwargs):
        # already admin-only, but keep explicit
        if not request.user.is_staff:
            raise PermissionDenied("Admin only.")
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Admin only.")
        return super().retrieve(request, *args, **kwargs)
