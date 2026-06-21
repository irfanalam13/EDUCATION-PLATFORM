from rest_framework import serializers
from .models import Notification, ScheduledNotification, Device


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "token", "platform", "is_active", "created_at"]
        read_only_fields = ["is_active", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "type",
            "data",
            "is_read",
            "read_at",
            "created_at",
        ]


class NotificationReadSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=False,
    )
    all = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        ids = attrs.get("ids")
        mark_all = attrs.get("all", False)

        if not ids and not mark_all:
            raise serializers.ValidationError("Provide `ids` or set `all=true`.")
        if ids and mark_all:
            raise serializers.ValidationError("Use either `ids` OR `all=true`, not both.")
        return attrs


# Optional (admin use later)
class ScheduledNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledNotification
        fields = [
            "id",
            "user",
            "title",
            "body",
            "type",
            "data",
            "send_at",
            "status",
            "last_error",
            "created_at",
        ]
        read_only_fields = ["status", "last_error", "created_at"]
