from django.contrib import admin
from .models import Notification, ScheduledNotification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "title", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("title", "body", "user__username", "user__email")
    ordering = ("-created_at",)


@admin.register(ScheduledNotification)
class ScheduledNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "type", "title", "send_at", "status", "created_at")
    list_filter = ("status", "type")
    search_fields = ("title", "body", "user__username", "user__email")
    ordering = ("send_at",)
