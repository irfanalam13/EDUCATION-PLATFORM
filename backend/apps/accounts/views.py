from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Profile, User
from .permissions import IsAdmin, IsTeacherOrAdmin
from .serializers import (
    EmailOTPResendSerializer,
    EmailOTPVerifySerializer,
    GoogleAuthSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    TeacherRequestListSerializer,
    UserAdminListSerializer,
    UserRoleUpdateSerializer,
)
from .services import (
    attach_auth_cookies,
    authenticate_google_id_token,
    clear_auth_cookies,
    issue_tokens_for_user,
    reset_password,
    send_email_verification_otp,
    send_password_reset_otp,
    verify_email_otp,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    dev_otp = send_email_verification_otp(user=user) if settings.ACCOUNT_EMAIL_VERIFICATION_REQUIRED else None
    payload = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "email_verified": user.email_verified,
        "requires_verification": settings.ACCOUNT_EMAIL_VERIFICATION_REQUIRED and not user.email_verified,
    }
    if dev_otp:
        payload["dev_otp"] = dev_otp
    return Response(payload, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email_view(request):
    serializer = EmailOTPVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = verify_email_otp(**serializer.validated_data)
    return Response({"detail": "Email verified.", "user": MeSerializer(user).data})


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_verification_view(request):
    serializer = EmailOTPResendSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].strip().lower()
    user = User.objects.filter(email__iexact=email).first()
    if user and not user.email_verified:
        dev_otp = send_email_verification_otp(user=user)
    else:
        dev_otp = None

    payload = {"detail": "If this email needs verification, a new code has been sent."}
    if dev_otp:
        payload["dev_otp"] = dev_otp
    return Response(payload)


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    dev_otp = send_password_reset_otp(email=serializer.validated_data["email"])
    payload = {"detail": "If an account exists for that email, a reset code has been sent."}
    if dev_otp:
        payload["dev_otp"] = dev_otp
    return Response(payload)


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reset_password(
        email=serializer.validated_data["email"],
        code=serializer.validated_data["code"],
        new_password=serializer.validated_data["new_password"],
    )
    return Response({"detail": "Password has been reset. You can now sign in."})


@api_view(["POST"])
@permission_classes([AllowAny])
def google_auth_view(request):
    serializer = GoogleAuthSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate_google_id_token(id_token_value=serializer.validated_data["id_token"])
    access, refresh = issue_tokens_for_user(user)
    response = Response({"access": access, "refresh": refresh, "user": MeSerializer(user).data})
    attach_auth_cookies(response, access=access, refresh=refresh)
    return response


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me_view(request):
    if request.method == "GET":
        return Response(MeSerializer(request.user).data)

    serializer = MeSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


class DevTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        if username:
            user = User.objects.filter(username=username).first()
            if user and not user.is_active and not user.email_verified:
                return Response(
                    {"detail": "Email verification required.", "code": "email_verification_required", "email": user.email},
                    status=status.HTTP_403_FORBIDDEN,
                )
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK and "access" in response.data and "refresh" in response.data:
            attach_auth_cookies(response, access=response.data["access"], refresh=response.data["refresh"])
        return response


class CookieTokenRefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "refresh"

    def post(self, request, *args, **kwargs):
        refresh_cookie_name = settings.JWT_REFRESH_COOKIE_NAME
        if not request.data.get("refresh"):
            data = request.data.copy()
            data["refresh"] = request.COOKIES.get(refresh_cookie_name)
            request._full_data = data

        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK and "access" in response.data:
            refresh_token = response.data.get("refresh") or request.data.get("refresh")
            attach_auth_cookies(response, access=response.data["access"], refresh=refresh_token)
        return response


class AdminTeacherRequestsViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = TeacherRequestListSerializer

    def get_queryset(self):
        queryset = Profile.objects.select_related("user").all().order_by("-teacher_applied_at")
        teacher_status = self.request.query_params.get("status")
        if teacher_status:
            return queryset.filter(teacher_status=teacher_status)
        return queryset.filter(teacher_status=Profile.TeacherStatus.PENDING)

    @action(detail=True, methods=["patch"])
    def approve(self, request, pk=None):
        profile = self.get_object()
        profile.teacher_status = Profile.TeacherStatus.APPROVED
        profile.teacher_reviewed_at = timezone.now()
        profile.save(update_fields=["teacher_status", "teacher_reviewed_at"])

        user = profile.user
        user.role = User.Role.TEACHER
        user.save(update_fields=["role"])

        return Response(self.get_serializer(profile).data)

    @action(detail=True, methods=["patch"])
    def reject(self, request, pk=None):
        profile = self.get_object()
        profile.teacher_status = Profile.TeacherStatus.REJECTED
        profile.teacher_reviewed_at = timezone.now()
        profile.save(update_fields=["teacher_status", "teacher_reviewed_at"])
        return Response(self.get_serializer(profile).data)


class MeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response(MeSerializer(request.user).data)

    def partial_update(self, request):
        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserReadViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.select_related("profile").all()
    serializer_class = UserAdminListSerializer
    permission_classes = [IsTeacherOrAdmin]


class AdminUserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserAdminListSerializer
    permission_classes = [IsAdmin]

    @action(detail=True, methods=["patch"], url_path="role")
    def set_role(self, request, pk=None):
        user = self.get_object()
        serializer = UserRoleUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserAdminListSerializer(user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    refresh_cookie_name = settings.JWT_REFRESH_COOKIE_NAME
    refresh = request.data.get("refresh") or request.COOKIES.get(refresh_cookie_name)
    if not refresh:
        return Response({"detail": "refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh)
        token.blacklist()
    except TokenError:
        return Response({"detail": "invalid token"}, status=status.HTTP_400_BAD_REQUEST)

    response = Response({"detail": "logged out"}, status=status.HTTP_200_OK)
    clear_auth_cookies(response)
    return response
