from __future__ import annotations

from datetime import timedelta

from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import reports, services
from .models import AnalyticsReport
from .permissions import (
    CanViewStudentAnalytics,
    CanViewTeacherAnalytics,
    IsInstitutionAdmin,
)
from .serializers import AnalyticsReportSerializer, ReportGenerateSerializer


def _days(request, default: int = 30, lo: int = 1, hi: int = 365) -> int:
    try:
        d = int(request.query_params.get("days", default))
    except (TypeError, ValueError):
        d = default
    return max(lo, min(hi, d))


def _int(request, key):
    val = request.query_params.get(key)
    return int(val) if val and val.isdigit() else None


class InstitutionAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get(self, request):
        institution_id = _int(request, "institution_id")
        return Response(services.institution_overview(institution_id, days=_days(request)))


class TeacherAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, CanViewTeacherAnalytics]

    def get(self, request):
        institution_id = _int(request, "institution_id")
        teacher_id = _int(request, "teacher_id") or request.user.id
        return Response(
            services.teacher_overview(institution_id, teacher_id, days=_days(request))
        )


class StudentAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, CanViewStudentAnalytics]

    def get(self, request):
        student_id = _int(request, "student_id") or request.user.id
        return Response(services.student_overview(student_id, days=_days(request)))


class SubjectAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get(self, request):
        institution_id = _int(request, "institution_id")
        subject_id = _int(request, "subject_id")
        return Response(
            services.subject_analytics(institution_id, subject_id=subject_id, days=_days(request, default=90))
        )


class ReportListView(APIView):
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    def get(self, request):
        institution_id = _int(request, "institution_id")
        qs = AnalyticsReport.objects.filter(institution_id=institution_id)
        data = AnalyticsReportSerializer(qs, many=True, context={"request": request}).data
        return Response(data)


class ReportGenerateView(APIView):
    permission_classes = [IsAuthenticated, IsInstitutionAdmin]

    # Window lengths for non-custom periods.
    _PERIOD_DAYS = {
        AnalyticsReport.Period.MONTHLY: 30,
        AnalyticsReport.Period.SEMESTER: 180,
    }

    def post(self, request):
        serializer = ReportGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data["scope"] != AnalyticsReport.Scope.INSTITUTION:
            return Response(
                {"detail": "Only INSTITUTION reports are supported in this release."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        today = timezone.localdate()
        if data.get("period_start") and data.get("period_end"):
            start, end = data["period_start"], data["period_end"]
            if end < start:
                return Response(
                    {"detail": "period_end must be on or after period_start."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            span = self._PERIOD_DAYS.get(data["period"], 30)
            end = today
            start = today - timedelta(days=span - 1)

        institution_id = data["institution_id"]
        fmt = data["file_format"]
        title = "Institution analytics report"

        report = AnalyticsReport(
            institution_id=institution_id,
            scope=data["scope"],
            period=data["period"],
            file_format=fmt,
            title=title,
            period_start=start,
            period_end=end,
            created_by=request.user,
            status=AnalyticsReport.Status.PENDING,
        )
        try:
            payload = reports.render_institution_report(institution_id, fmt, start, end, title)
            ext = "xlsx" if fmt == AnalyticsReport.Format.XLSX else "pdf"
            filename = f"institution_{institution_id}_{start}_{end}.{ext}"
            report.file.save(filename, ContentFile(payload), save=False)
            report.status = AnalyticsReport.Status.READY
            report.save()
        except Exception:
            report.status = AnalyticsReport.Status.FAILED
            report.save()
            raise

        return Response(
            AnalyticsReportSerializer(report, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
