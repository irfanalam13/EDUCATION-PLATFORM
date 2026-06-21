from rest_framework import serializers
from .models import Report, ContentFlag


class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["target_type", "target_id", "reason", "message"]

    def create(self, validated_data):
        request = self.context["request"]
        return Report.objects.create(reporter=request.user, **validated_data)


class ReportAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["status", "resolved_note"]

    def update(self, instance, validated_data):
        request = self.context["request"]
        instance.status = validated_data.get("status", instance.status)
        instance.resolved_note = validated_data.get("resolved_note", instance.resolved_note)

        # If admin moves away from open/reviewing, mark resolver automatically.
        if instance.status in [Report.Status.RESOLVED, Report.Status.REJECTED]:
            instance.resolved_by = request.user

        instance.save()
        return instance


class ReportReadSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(source="reporter.username", read_only=True)
    resolved_by_username = serializers.CharField(source="resolved_by.username", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "reporter_username",
            "target_type",
            "target_id",
            "reason",
            "message",
            "status",
            "resolved_by",
            "resolved_by_username",
            "resolved_note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ContentFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentFlag
        fields = [
            "id",
            "target_type",
            "target_id",
            "flag_type",
            "severity",
            "is_active",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]
