from django.urls import path

from .views import (
    InstitutionAnalyticsView,
    ReportGenerateView,
    ReportListView,
    StudentAnalyticsView,
    SubjectAnalyticsView,
    TeacherAnalyticsView,
)

urlpatterns = [
    path("institution/", InstitutionAnalyticsView.as_view(), name="analytics-institution"),
    path("teacher/", TeacherAnalyticsView.as_view(), name="analytics-teacher"),
    path("student/", StudentAnalyticsView.as_view(), name="analytics-student"),
    path("subject/", SubjectAnalyticsView.as_view(), name="analytics-subject"),
    path("reports/", ReportListView.as_view(), name="analytics-reports"),
    path("report/generate/", ReportGenerateView.as_view(), name="analytics-report-generate"),
]
