from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification, Device
from .serializers import NotificationSerializer, NotificationReadSerializer, DeviceSerializer
from .services import mark_notifications_read


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.for_user(self.request.user)

        # filters (optional)
        unread = self.request.query_params.get("unread")
        if unread in ("1", "true", "True"):
            qs = qs.filter(is_read=False)

        ntype = self.request.query_params.get("type")
        if ntype:
            qs = qs.filter(type=ntype)

        return qs

    @action(detail=False, methods=["post"], url_path="read")
    def read(self, request):
        """
        POST /api/notifications/read/
        Body: {"ids":[...]} OR {"all": true}
        """
        ser = NotificationReadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        ids = ser.validated_data.get("ids")
        mark_all = ser.validated_data.get("all", False)

        updated = mark_notifications_read(user=request.user, ids=ids, mark_all=mark_all)
        return Response({"ok": True, "updated": updated}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = Notification.objects.for_user(request.user).unread().count()
        return Response({"unread": count}, status=status.HTTP_200_OK)


class DeviceViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Register/unregister Expo push tokens for the current user."""

    permission_classes = [IsAuthenticated]
    serializer_class = DeviceSerializer

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user, is_active=True)

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token = ser.validated_data["token"]
        platform = ser.validated_data.get("platform", Device.Platform.ANDROID)
        # Upsert by token so re-registering the same device just refreshes ownership.
        device, _ = Device.objects.update_or_create(
            token=token,
            defaults={"user": request.user, "platform": platform, "is_active": True},
        )
        return Response(DeviceSerializer(device).data, status=status.HTTP_201_CREATED)
