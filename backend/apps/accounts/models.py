from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        TEACHER = "TEACHER", "Teacher"
        AUTHOR = "AUTHOR", "Author"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )
    email_verified = models.BooleanField(default=False, db_index=True)
    auth_provider = models.CharField(
        max_length=20,
        choices=[("password", "Password"), ("google", "Google")],
        default="password",
        db_index=True,
    )
    google_sub = models.CharField(max_length=255, blank=True, null=True, unique=True)

    # Optional: if you want email login later, enforce unique email:
    # email = models.EmailField(unique=True)


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # Student info (adjust as needed)
    student_class = models.CharField(max_length=50, blank=True)     # e.g. "10", "+2", "BSc CSIT"
    college = models.CharField(max_length=150, blank=True)

    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)

    class TeacherStatus(models.TextChoices):
        NONE = "NONE", "None"
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    teacher_status = models.CharField(
        max_length=20,
        choices=TeacherStatus.choices,
        default=TeacherStatus.NONE,
        db_index=True,
    )
    teacher_message = models.TextField(blank=True)
    teacher_applied_at = models.DateTimeField(null=True, blank=True)
    teacher_reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Profile({self.user_id})"




class RefreshTokenBlacklist(models.Model):
    token = models.TextField()
    blacklisted_at = models.DateTimeField(auto_now_add=True)
#(optional if you use SimpleJWT blacklist app)


class EmailOTP(models.Model):
    class Purpose(models.TextChoices):
        VERIFY_EMAIL = "VERIFY_EMAIL", "Verify email"
        RESET_PASSWORD = "RESET_PASSWORD", "Reset password"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_otps")
    email = models.EmailField(db_index=True)
    purpose = models.CharField(max_length=32, choices=Purpose.choices, default=Purpose.VERIFY_EMAIL)
    code_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "purpose", "consumed_at"]),
            models.Index(fields=["email", "purpose", "expires_at"]),
        ]
        ordering = ["-created_at"]

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    def set_code(self, raw_code: str) -> None:
        self.code_hash = make_password(raw_code)

    def check_code(self, raw_code: str) -> bool:
        return check_password(raw_code, self.code_hash)
