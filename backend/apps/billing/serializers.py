from __future__ import annotations

from rest_framework import serializers

from . import features as feat
from .gateways import SUPPORTED_GATEWAYS
from .models import Coupon, InstitutionSubscription, Invoice, Payment, Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    is_free = serializers.BooleanField(read_only=True)
    features = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            "id", "tier", "name", "slug", "description", "price", "currency",
            "interval", "trial_days", "max_seats", "highlight", "display_order",
            "is_free", "features",
        ]

    def get_features(self, obj):
        """Authoritative capability list derived from the tier (with quotas)."""
        return [
            {"key": key, "label": feat.FEATURE_LABELS.get(key, key), "limit": limit}
            for key, limit in feat.features_for_tier(obj.tier).items()
        ]


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ["code", "description", "percent_off", "amount_off", "currency", "duration", "valid_until"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "gateway", "gateway_payment_id", "amount", "currency",
            "amount_refunded", "status", "method", "created_at", "processed_at",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    amount_due = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "number", "status", "currency", "subtotal", "discount_amount",
            "tax_amount", "total", "amount_paid", "amount_due", "line_items",
            "issued_at", "paid_at", "due_date", "created_at", "payments",
        ]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    in_trial = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id", "plan", "status", "gateway", "started_at", "trial_end",
            "current_period_start", "current_period_end", "cancel_at_period_end",
            "canceled_at", "is_active", "in_trial", "created_at",
        ]


class InstitutionSubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = InstitutionSubscription
        fields = [
            "id", "institution", "plan", "seats", "billing_email", "status",
            "current_period_start", "current_period_end", "is_active", "created_at",
        ]


class SubscribeRequestSerializer(serializers.Serializer):
    plan = serializers.SlugRelatedField(slug_field="slug", queryset=Plan.objects.filter(is_active=True))
    gateway = serializers.ChoiceField(choices=SUPPORTED_GATEWAYS, default="MANUAL")
    coupon_code = serializers.CharField(required=False, allow_blank=True, default="")
    success_url = serializers.URLField(required=False, allow_blank=True, default="")
    cancel_url = serializers.URLField(required=False, allow_blank=True, default="")
    start_trial = serializers.BooleanField(default=True)
    # Institution purchases:
    institution_id = serializers.IntegerField(required=False)
    seats = serializers.IntegerField(required=False, default=1, min_value=1)
    billing_email = serializers.EmailField(required=False, allow_blank=True, default="")


class CancelRequestSerializer(serializers.Serializer):
    at_period_end = serializers.BooleanField(default=False)


class RefundRequestSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    cancel_subscription = serializers.BooleanField(default=False)
