from django.contrib import admin
from .models import Report, ContentFlag


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "reason",
        "target_type",
        "target_id",
        "reporter",
        "created_at",
    )
    list_filter = ("status", "reason", "target_type", "created_at")
    search_fields = ("target_id", "reporter__username", "message", "resolved_note")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ContentFlag)
class ContentFlagAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "flag_type",
        "severity",
        "is_active",
        "target_type",
        "target_id",
        "created_by",
        "created_at",
    )
    list_filter = ("flag_type", "is_active", "created_at")
    search_fields = ("target_id", "target_type")
    readonly_fields = ("created_at",)
