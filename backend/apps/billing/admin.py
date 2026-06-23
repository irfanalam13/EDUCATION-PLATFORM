from __future__ import annotations

from django.contrib import admin

from .models import (
    Coupon,
    FeatureAccess,
    InstitutionSubscription,
    Invoice,
    Payment,
    Plan,
    Subscription,
    WebhookEvent,
)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "tier", "price", "currency", "interval", "is_active", "is_public", "display_order")
    list_filter = ("tier", "interval", "is_active", "is_public")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "percent_off", "amount_off", "duration", "redeemed_count", "is_active")
    list_filter = ("duration", "is_active")
    search_fields = ("code",)
    filter_horizontal = ("applies_to_plans",)


class InvoiceInline(admin.TabularInline):
    model = Invoice
    extra = 0
    fields = ("number", "status", "total", "amount_paid", "created_at")
    readonly_fields = ("number", "created_at")
    show_change_link = True


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "gateway", "current_period_end", "cancel_at_period_end")
    list_filter = ("status", "gateway", "plan__tier")
    search_fields = ("user__username", "user__email", "gateway_subscription_id")
    autocomplete_fields = ("user", "plan", "coupon")
    inlines = [InvoiceInline]


@admin.register(InstitutionSubscription)
class InstitutionSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("institution", "plan", "seats", "status", "current_period_end")
    list_filter = ("status", "plan__tier")
    search_fields = ("institution__name", "billing_email")
    # Institution's admin doesn't enable search_fields, so don't autocomplete it.
    autocomplete_fields = ("plan", "coupon", "purchased_by")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("gateway", "gateway_payment_id", "amount", "status", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "total", "amount_paid", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("number", "user__username", "user__email")
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("gateway", "gateway_payment_id", "amount", "status", "created_at")
    list_filter = ("gateway", "status")
    search_fields = ("gateway_payment_id", "invoice__number")


@admin.register(FeatureAccess)
class FeatureAccessAdmin(admin.ModelAdmin):
    list_display = ("feature", "user", "institution", "is_enabled", "limit", "used", "source")
    list_filter = ("feature", "is_enabled", "source")
    search_fields = ("feature", "user__username", "institution__name")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("gateway", "event_id", "event_type", "signature_verified", "processed", "created_at")
    list_filter = ("gateway", "processed", "signature_verified")
    search_fields = ("event_id", "event_type")
    readonly_fields = ("gateway", "event_id", "event_type", "payload", "created_at")
