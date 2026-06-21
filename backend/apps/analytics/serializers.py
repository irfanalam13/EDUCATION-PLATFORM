from __future__ import annotations

from rest_framework import serializers

from .models import AnalyticsReport


class AnalyticsReportSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = AnalyticsReport
        fields = [
            "id",
            "institution",
            "scope",
            "period",
            "file_format",
            "title",
            "period_start",
            "period_end",
            "status",
            "download_url",
            "created_at",
        ]
        read_only_fields = fields

    def get_download_url(self, obj) -> str | None:
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class ReportGenerateSerializer(serializers.Serializer):
    institution_id = serializers.IntegerField()
    scope = serializers.ChoiceField(
        choices=AnalyticsReport.Scope.choices, default=AnalyticsReport.Scope.INSTITUTION
    )
    period = serializers.ChoiceField(
        choices=AnalyticsReport.Period.choices, default=AnalyticsReport.Period.MONTHLY
    )
    file_format = serializers.ChoiceField(
        choices=AnalyticsReport.Format.choices, default=AnalyticsReport.Format.PDF
    )
    # Optional explicit window; defaults derived from `period` when omitted.
    period_start = serializers.DateField(required=False)
    period_end = serializers.DateField(required=False)
