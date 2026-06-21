from __future__ import annotations

import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils import timezone

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailOTP, Profile


User = get_user_model()


def register_user(*, validated_data: dict) -> User:
    validated_data = validated_data.copy()
    password = validated_data.pop("password")
    validated_data.pop("password2", None)

    account_type = validated_data.pop("account_type", User.Role.STUDENT)
    teacher_message = validated_data.pop("teacher_message", "")

    user = User(**validated_data)
    if settings.ACCOUNT_EMAIL_VERIFICATION_REQUIRED:
        user.is_active = False
        user.email_verified = False
    user.set_password(password)
    user.save()

    if account_type == User.Role.TEACHER:
        profile = user.profile
        profile.teacher_status = Profile.TeacherStatus.PENDING
        profile.teacher_message = teacher_message
        profile.teacher_applied_at = timezone.now()
        profile.save(update_fields=["teacher_status", "teacher_message", "teacher_applied_at"])

    return user


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def create_email_otp(*, user: User, purpose: str = EmailOTP.Purpose.VERIFY_EMAIL) -> tuple[EmailOTP, str]:
    now = timezone.now()
    EmailOTP.objects.filter(user=user, purpose=purpose, consumed_at__isnull=True).update(consumed_at=now)

    raw_code = generate_otp_code()
    otp = EmailOTP(
        user=user,
        email=user.email,
        purpose=purpose,
        expires_at=now + timedelta(minutes=settings.EMAIL_OTP_EXPIRY_MINUTES),
    )
    otp.set_code(raw_code)
    otp.save()
    return otp, raw_code


def send_email_verification_otp(*, user: User) -> str | None:
    _otp, raw_code = create_email_otp(user=user)
    send_mail(
        subject="Verify your EduPlatform account",
        message=(
            f"Your EduPlatform verification code is {raw_code}. "
            f"It expires in {settings.EMAIL_OTP_EXPIRY_MINUTES} minutes."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return raw_code if settings.DEBUG else None


def verify_email_otp(*, email: str, code: str) -> User:
    normalized_email = email.strip().lower()
    user = User.objects.filter(email__iexact=normalized_email).first()
    if not user:
        raise ValidationError({"email": "No account exists for this email."})

    otp = (
        EmailOTP.objects.filter(
            user=user,
            email__iexact=normalized_email,
            purpose=EmailOTP.Purpose.VERIFY_EMAIL,
            consumed_at__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )
    if not otp:
        raise ValidationError({"code": "Verification code not found. Please request a new code."})

    if otp.is_expired:
        otp.consumed_at = timezone.now()
        otp.save(update_fields=["consumed_at"])
        raise ValidationError({"code": "Verification code has expired."})

    if otp.attempts >= otp.max_attempts:
        otp.consumed_at = timezone.now()
        otp.save(update_fields=["consumed_at"])
        raise ValidationError({"code": "Too many attempts. Please request a new code."})

    otp.attempts += 1
    if not otp.check_code(code.strip()):
        otp.save(update_fields=["attempts"])
        raise ValidationError({"code": "Invalid verification code."})

    otp.consumed_at = timezone.now()
    otp.save(update_fields=["attempts", "consumed_at"])

    user.email_verified = True
    user.is_active = True
    user.save(update_fields=["email_verified", "is_active"])
    return user


def send_password_reset_otp(*, email: str) -> str | None:
    """Send a password-reset code. Non-enumerating: silently no-ops for unknown
    emails so callers can always return the same response."""
    normalized_email = email.strip().lower()
    user = User.objects.filter(email__iexact=normalized_email).first()
    if not user:
        return None
    _otp, raw_code = create_email_otp(user=user, purpose=EmailOTP.Purpose.RESET_PASSWORD)
    send_mail(
        subject="Reset your EduPlatform password",
        message=(
            f"Your EduPlatform password reset code is {raw_code}. "
            f"It expires in {settings.EMAIL_OTP_EXPIRY_MINUTES} minutes. "
            f"If you did not request this, you can safely ignore this email."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return raw_code if settings.DEBUG else None


def reset_password(*, email: str, code: str, new_password: str) -> User:
    normalized_email = email.strip().lower()
    user = User.objects.filter(email__iexact=normalized_email).first()
    if not user:
        raise ValidationError({"email": "No account exists for this email."})

    otp = (
        EmailOTP.objects.filter(
            user=user,
            email__iexact=normalized_email,
            purpose=EmailOTP.Purpose.RESET_PASSWORD,
            consumed_at__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )
    if not otp:
        raise ValidationError({"code": "Reset code not found. Please request a new code."})

    if otp.is_expired:
        otp.consumed_at = timezone.now()
        otp.save(update_fields=["consumed_at"])
        raise ValidationError({"code": "Reset code has expired."})

    if otp.attempts >= otp.max_attempts:
        otp.consumed_at = timezone.now()
        otp.save(update_fields=["consumed_at"])
        raise ValidationError({"code": "Too many attempts. Please request a new code."})

    otp.attempts += 1
    if not otp.check_code(code.strip()):
        otp.save(update_fields=["attempts"])
        raise ValidationError({"code": "Invalid reset code."})

    otp.consumed_at = timezone.now()
    otp.save(update_fields=["attempts", "consumed_at"])

    user.set_password(new_password)
    # A verified reset implies the user controls the mailbox.
    user.is_active = True
    user.save(update_fields=["password", "is_active"])
    return user


def authenticate_google_id_token(*, id_token_value: str) -> User:
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token as google_id_token
    except ImportError as exc:
        raise ValidationError({"google": "Google auth support is not installed."}) from exc

    client_ids = settings.GOOGLE_OAUTH_CLIENT_IDS
    if not client_ids:
        raise ValidationError({"google": "GOOGLE_OAUTH_CLIENT_IDS is not configured."})

    verified_payload = None
    request = google_requests.Request()
    for client_id in client_ids:
        try:
            verified_payload = google_id_token.verify_oauth2_token(id_token_value, request, client_id)
            break
        except ValueError:
            continue

    if not verified_payload:
        raise ValidationError({"google": "Invalid Google credential."})

    email = str(verified_payload.get("email") or "").strip().lower()
    sub = str(verified_payload.get("sub") or "").strip()
    if not email or not sub:
        raise ValidationError({"google": "Google credential did not include email/sub."})

    if verified_payload.get("email_verified") is False:
        raise ValidationError({"google": "Google account email is not verified."})

    user = User.objects.filter(google_sub=sub).first() or User.objects.filter(email__iexact=email).first()
    if user is None:
        base_username = email.split("@", 1)[0].replace(".", "_")[:130] or "google_user"
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_username}_{suffix}"
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=verified_payload.get("given_name", ""),
            last_name=verified_payload.get("family_name", ""),
        )

    user.google_sub = sub
    user.auth_provider = "google"
    user.email_verified = True
    user.is_active = True
    user.save(update_fields=["google_sub", "auth_provider", "email_verified", "is_active"])
    return user


def issue_tokens_for_user(user: User) -> tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def attach_auth_cookies(response: Response | HttpResponse, *, access: str, refresh: str) -> Response | HttpResponse:
    response.set_cookie(
        settings.JWT_ACCESS_COOKIE_NAME,
        access,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        path="/",
    )
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        refresh,
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        path="/",
    )
    return response


def clear_auth_cookies(response: Response | HttpResponse) -> Response | HttpResponse:
    response.delete_cookie(settings.JWT_ACCESS_COOKIE_NAME, path="/", samesite=settings.JWT_COOKIE_SAMESITE)
    response.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME, path="/", samesite=settings.JWT_COOKIE_SAMESITE)
    return response
