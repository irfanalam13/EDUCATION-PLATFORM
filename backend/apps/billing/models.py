"""Billing & subscription domain models.

One source of truth for plans, subscriptions (individual + institution),
invoices, payments, coupons, per-user/institution feature access, and the
webhook event log used for idempotent gateway callbacks.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

DEFAULT_CURRENCY = getattr(settings, "BILLING_DEFAULT_CURRENCY", "NPR")
ZERO = Decimal("0.00")


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Gateway(models.TextChoices):
    STRIPE = "STRIPE", "Stripe"
    KHALTI = "KHALTI", "Khalti"
    ESEWA = "ESEWA", "eSewa"
    MANUAL = "MANUAL", "Manual"


class BillingInterval(models.TextChoices):
    MONTH = "MONTH", "Monthly"
    YEAR = "YEAR", "Yearly"
    LIFETIME = "LIFETIME", "Lifetime"


class Plan(TimeStampedModel):
    """A purchasable subscription plan. Tier drives feature entitlements."""

    class Tier(models.TextChoices):
        FREE = "FREE", "Free"
        PREMIUM = "PREMIUM", "Premium"
        INSTITUTION = "INSTITUTION", "Institution"

    tier = models.CharField(max_length=16, choices=Tier.choices)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=ZERO, validators=[MinValueValidator(ZERO)]
    )
    currency = models.CharField(max_length=8, default=DEFAULT_CURRENCY)
    interval = models.CharField(
        max_length=16, choices=BillingInterval.choices, default=BillingInterval.MONTH
    )
    trial_days = models.PositiveIntegerField(default=0)
    # For per-seat institution plans, price is per seat; max_seats caps a purchase.
    max_seats = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    highlight = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    stripe_price_id = models.CharField(max_length=120, blank=True, default="")
    feature_list = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["display_order", "price"]
        indexes = [
            models.Index(fields=["tier"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_interval_display()})"

    @property
    def is_free(self) -> bool:
        return self.tier == self.Tier.FREE or self.price <= ZERO


class Coupon(TimeStampedModel):
    class Duration(models.TextChoices):
        ONCE = "ONCE", "Once"
        REPEATING = "REPEATING", "Repeating"
        FOREVER = "FOREVER", "Forever"

    code = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=200, blank=True, default="")
    percent_off = models.PositiveIntegerField(null=True, blank=True)
    amount_off = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default=DEFAULT_CURRENCY)
    duration = models.CharField(max_length=16, choices=Duration.choices, default=Duration.ONCE)
    duration_in_months = models.PositiveIntegerField(null=True, blank=True)
    max_redemptions = models.PositiveIntegerField(null=True, blank=True)
    redeemed_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    applies_to_plans = models.ManyToManyField(Plan, blank=True, related_name="coupons")
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.code

    def is_valid(self, plan=None, when=None) -> bool:
        when = when or timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and when < self.valid_from:
            return False
        if self.valid_until and when > self.valid_until:
            return False
        if self.max_redemptions is not None and self.redeemed_count >= self.max_redemptions:
            return False
        if plan is not None and self.applies_to_plans.exists():
            if not self.applies_to_plans.filter(pk=plan.pk).exists():
                return False
        return True

    def discount_for(self, amount: Decimal) -> Decimal:
        """Return the discount amount (never more than ``amount``)."""
        if amount <= ZERO:
            return ZERO
        if self.percent_off:
            disc = (amount * Decimal(self.percent_off) / Decimal("100")).quantize(Decimal("0.01"))
        elif self.amount_off:
            disc = self.amount_off
        else:
            disc = ZERO
        return min(disc, amount)


class SubscriptionStatus(models.TextChoices):
    TRIALING = "TRIALING", "Trialing"
    ACTIVE = "ACTIVE", "Active"
    PAST_DUE = "PAST_DUE", "Past due"
    CANCELED = "CANCELED", "Canceled"
    EXPIRED = "EXPIRED", "Expired"
    INCOMPLETE = "INCOMPLETE", "Incomplete"


# Statuses that represent a "live" (currently-occupying) subscription slot.
LIVE_STATUSES = [
    SubscriptionStatus.TRIALING,
    SubscriptionStatus.ACTIVE,
    SubscriptionStatus.PAST_DUE,
    SubscriptionStatus.INCOMPLETE,
]
# Statuses a paying/trialing subscriber holds (used by analytics + entitlements).
PAYING_STATUSES = [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING, SubscriptionStatus.PAST_DUE]


class BillingState(TimeStampedModel):
    """Lifecycle fields shared by individual and institution subscriptions."""

    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=16, choices=SubscriptionStatus.choices, default=SubscriptionStatus.INCOMPLETE
    )
    gateway = models.CharField(max_length=16, choices=Gateway.choices, default=Gateway.MANUAL)
    gateway_subscription_id = models.CharField(max_length=200, blank=True, default="")
    gateway_customer_id = models.CharField(max_length=200, blank=True, default="")
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_active(self) -> bool:
        """Currently entitled to paid features (trial counts as active)."""
        if self.status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING):
            return False
        if self.current_period_end and self.current_period_end < timezone.now():
            return False
        return True

    @property
    def in_trial(self) -> bool:
        if self.status != SubscriptionStatus.TRIALING:
            return False
        return not self.trial_end or self.trial_end > timezone.now()


class Subscription(BillingState):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")

    class Meta:
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["current_period_end"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status__in=["TRIALING", "ACTIVE", "PAST_DUE", "INCOMPLETE"]),
                name="uniq_live_subscription_per_user",
            )
        ]

    def __str__(self) -> str:
        return f"Subscription(user={self.user_id}, plan={self.plan_id}, {self.status})"


class InstitutionSubscription(BillingState):
    institution = models.OneToOneField(
        "institutions.Institution", on_delete=models.CASCADE, related_name="subscription"
    )
    seats = models.PositiveIntegerField(default=1)
    billing_email = models.EmailField(blank=True, default="")
    purchased_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["current_period_end"]),
        ]

    def __str__(self) -> str:
        return f"InstitutionSubscription(inst={self.institution_id}, {self.status})"


class Invoice(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Open"
        PAID = "PAID", "Paid"
        VOID = "VOID", "Void"
        UNCOLLECTIBLE = "UNCOLLECTIBLE", "Uncollectible"
        REFUNDED = "REFUNDED", "Refunded"

    number = models.CharField(max_length=40, unique=True, blank=True)
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices"
    )
    institution_subscription = models.ForeignKey(
        InstitutionSubscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    currency = models.CharField(max_length=8, default=DEFAULT_CURRENCY)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    line_items = models.JSONField(default=list, blank=True)
    gateway_invoice_id = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Invoice {self.number or self.pk} ({self.status})"

    @property
    def amount_due(self) -> Decimal:
        return max(ZERO, self.total - self.amount_paid)

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = f"INV-{timezone.now():%Y%m}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class Payment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCEEDED = "SUCCEEDED", "Succeeded"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"
        PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially refunded"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    gateway = models.CharField(max_length=16, choices=Gateway.choices)
    gateway_payment_id = models.CharField(max_length=200, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    currency = models.CharField(max_length=8, default=DEFAULT_CURRENCY)
    amount_refunded = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    method = models.CharField(max_length=40, blank=True, default="")
    idempotency_key = models.CharField(max_length=120, blank=True, default="")
    raw_payload = models.JSONField(default=dict, blank=True)
    error_message = models.CharField(max_length=300, blank=True, default="")
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["gateway", "gateway_payment_id"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["gateway", "gateway_payment_id"],
                condition=~models.Q(gateway_payment_id=""),
                name="uniq_gateway_payment_id",
            )
        ]

    def __str__(self) -> str:
        return f"Payment {self.gateway}:{self.gateway_payment_id or self.pk} ({self.status})"


class FeatureAccess(TimeStampedModel):
    """Per-user OR per-institution capability row with optional monthly quota."""

    class Source(models.TextChoices):
        PLAN = "PLAN", "Plan"
        TRIAL = "TRIAL", "Trial"
        MANUAL = "MANUAL", "Manual"
        COMP = "COMP", "Complimentary"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="feature_access"
    )
    institution = models.ForeignKey(
        "institutions.Institution",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="feature_access",
    )
    feature = models.CharField(max_length=60)
    is_enabled = models.BooleanField(default=True)
    limit = models.IntegerField(default=0)  # 0 == unlimited
    used = models.IntegerField(default=0)
    period_start = models.DateTimeField(null=True, blank=True)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.PLAN)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["institution"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "feature"],
                condition=models.Q(user__isnull=False),
                name="uniq_feature_per_user",
            ),
            models.UniqueConstraint(
                fields=["institution", "feature"],
                condition=models.Q(institution__isnull=False),
                name="uniq_feature_per_institution",
            ),
        ]

    def __str__(self) -> str:
        owner = f"user={self.user_id}" if self.user_id else f"inst={self.institution_id}"
        return f"FeatureAccess({owner}, {self.feature}, enabled={self.is_enabled})"

    @property
    def is_live(self) -> bool:
        return self.is_enabled and (self.expires_at is None or self.expires_at > timezone.now())

    @property
    def remaining(self):
        if self.limit <= 0:
            return None  # unlimited / unmetered
        return max(0, self.limit - self.used)


class WebhookEvent(TimeStampedModel):
    """Idempotency + audit log for inbound gateway webhooks."""

    gateway = models.CharField(max_length=16, choices=Gateway.choices)
    event_id = models.CharField(max_length=200)
    event_type = models.CharField(max_length=120, blank=True, default="")
    signature_verified = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    payload = models.JSONField(default=dict, blank=True)
    error = models.CharField(max_length=300, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["gateway", "event_id"], name="uniq_webhook_event")
        ]

    def __str__(self) -> str:
        return f"WebhookEvent({self.gateway}:{self.event_id})"
