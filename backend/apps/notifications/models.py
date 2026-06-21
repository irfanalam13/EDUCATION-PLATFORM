import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationType(models.TextChoices):
    SYSTEM = "SYSTEM", "System"
    XP = "XP", "XP"
    BADGE = "BADGE", "Badge"
    QUIZ = "QUIZ", "Quiz"
    ANNOUNCEMENT = "ANNOUNCEMENT", "Announcement"


class NotificationQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def unread(self):
        return self.filter(is_read=False)

    def mark_read(self):
        return self.update(is_read=True, read_at=timezone.now())


class Notification(models.Model):
    """
    In-app notification stored in DB.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    title = models.CharField(max_length=140)
    body = models.TextField(blank=True)

    type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )

    # deep link, metadata, etc. example: {"route":"/quiz/123"}
    data = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = NotificationQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} | {self.type} | {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class Device(models.Model):
    """A registered push target (Expo push token) for a user/device."""

    class Platform(models.TextChoices):
        IOS = "ios", "iOS"
        ANDROID = "android", "Android"
        WEB = "web", "Web"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
    )
    token = models.CharField(max_length=255, unique=True)  # Expo push token
    platform = models.CharField(max_length=16, choices=Platform.choices, default=Platform.ANDROID)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user", "is_active"])]

    def __str__(self):
        return f"Device(user={self.user_id}, {self.platform})"


class ScheduledStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SENT = "SENT", "Sent"
    CANCELLED = "CANCELLED", "Cancelled"
    FAILED = "FAILED", "Failed"


class ScheduledNotification(models.Model):
    """
    Optional: schedule future notifications.
    MVP: supports USER target. You can extend later to COHORT/ALL.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="scheduled_notifications_created",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scheduled_notifications",
    )

    title = models.CharField(max_length=140)
    body = models.TextField(blank=True)

    type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    data = models.JSONField(default=dict, blank=True)

    send_at = models.DateTimeField()

    status = models.CharField(
        max_length=16,
        choices=ScheduledStatus.choices,
        default=ScheduledStatus.PENDING,
    )
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["send_at"]
        indexes = [
            models.Index(fields=["status", "send_at"]),
            models.Index(fields=["user", "status", "send_at"]),
        ]

    def __str__(self):
        return f"{self.user_id} | {self.status} | {self.send_at}"
