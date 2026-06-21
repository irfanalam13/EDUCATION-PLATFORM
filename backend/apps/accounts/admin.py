from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import EmailOTP, User, Profile


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "username", "email", "role", "email_verified", "auth_provider", "is_active", "is_staff")
    list_filter = ("role", "email_verified", "auth_provider", "is_active", "is_staff")

    # add role field to User admin form
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Platform", {"fields": ("role", "email_verified", "auth_provider", "google_sub")}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "teacher_status",
        "teacher_applied_at",
        "teacher_reviewed_at",
    )
    list_filter = ("teacher_status",)
    search_fields = ("user__username", "user__email")


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "email", "purpose", "expires_at", "consumed_at", "attempts", "created_at")
    list_filter = ("purpose", "consumed_at")
    search_fields = ("user__username", "user__email", "email")
