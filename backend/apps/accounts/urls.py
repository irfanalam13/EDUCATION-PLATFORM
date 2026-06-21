from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
                    register_view, verify_email_view, resend_verification_view,
                    google_auth_view, me_view, MeViewSet,
                    AdminUserViewSet, UserReadViewSet,
                    logout_view, AdminTeacherRequestsViewSet,
                    DevTokenObtainPairView, CookieTokenRefreshView,
                    password_reset_request_view, password_reset_confirm_view,
)

router = DefaultRouter()
router.register(r"me", MeViewSet, basename="me")                 # /api/me/
router.register(r"users", UserReadViewSet, basename="users")     # /api/users/:id/
router.register(r"admin/users", AdminUserViewSet, basename="admin-users")  # /api/admin/users/
router.register(r"admin/teacher-requests", AdminTeacherRequestsViewSet, basename="admin-teacher-requests")


urlpatterns = [
    path("me/", me_view, name="me"),
    path("", include(router.urls)),
    path("auth/register/", register_view, name="register"),
    path("auth/verify-email/", verify_email_view, name="verify-email"),
    path("auth/resend-verification/", resend_verification_view, name="resend-verification"),
    path("auth/google/", google_auth_view, name="google-auth"),
    path("auth/password-reset/", password_reset_request_view, name="password-reset"),
    path("auth/password-reset/confirm/", password_reset_confirm_view, name="password-reset-confirm"),
    path("auth/token/", DevTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout/", logout_view, name="logout"),
]

