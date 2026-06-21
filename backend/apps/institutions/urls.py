from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    InstitutionViewSet, InstitutionMemberViewSet,
    BatchViewSet,
    EnrollmentViewSet,
    CoursePackViewSet, CoursePackItemViewSet,
    AssignmentViewSet,
    SubmissionViewSet,
    CertificateViewSet,
    ParentLinkViewSet,
    AuditLogViewSet,
)

router = DefaultRouter()
router.register(r"institutions", InstitutionViewSet, basename="institutions")
router.register(r"institution-members", InstitutionMemberViewSet, basename="institution-members")
router.register(r"batches", BatchViewSet, basename="batches")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollments")
router.register(r"course-packs", CoursePackViewSet, basename="course-packs")
router.register(r"course-pack-items", CoursePackItemViewSet, basename="course-pack-items")
router.register(r"assignments", AssignmentViewSet, basename="assignments")
router.register(r"submissions", SubmissionViewSet, basename="submissions")
router.register(r"certificates", CertificateViewSet, basename="certificates")
router.register(r"parents", ParentLinkViewSet, basename="parents")
router.register(r"audit", AuditLogViewSet, basename="audit")

urlpatterns = [
    path("", include(router.urls)),
]
