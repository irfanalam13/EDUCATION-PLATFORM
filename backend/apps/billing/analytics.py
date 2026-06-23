"""Revenue analytics: MRR, ARR, churn, conversion, revenue by plan.

All amounts are normalised to a monthly figure for MRR so yearly and monthly
plans are comparable. Pure reads — safe to call from the admin dashboard.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone

from .models import (
    BillingInterval,
    InstitutionSubscription,
    Invoice,
    Payment,
    Subscription,
    SubscriptionStatus,
    ZERO,
)

# Subscriptions that contribute recurring revenue / count as subscribers.
PAYING = [SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE, SubscriptionStatus.TRIALING]
RECURRING = [SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE]


def _monthly_amount(price: Decimal, interval: str, seats: int = 1) -> Decimal:
    seats = max(1, seats)
    if interval == BillingInterval.YEAR:
        monthly = price / Decimal("12")
    elif interval == BillingInterval.LIFETIME:
        monthly = ZERO
    else:
        monthly = price
    return (monthly * seats).quantize(Decimal("0.01"))


def mrr() -> Decimal:
    """Monthly Recurring Revenue across individual + institution subscriptions."""
    total = ZERO
    for sub in Subscription.objects.filter(status__in=RECURRING).select_related("plan"):
        total += _monthly_amount(sub.plan.price, sub.plan.interval)
    for isub in InstitutionSubscription.objects.filter(status__in=RECURRING).select_related("plan"):
        total += _monthly_amount(isub.plan.price, isub.plan.interval, isub.seats)
    return total.quantize(Decimal("0.01"))


def arr() -> Decimal:
    return (mrr() * 12).quantize(Decimal("0.01"))


def active_subscriber_count() -> int:
    return (
        Subscription.objects.filter(status__in=PAYING).count()
        + InstitutionSubscription.objects.filter(status__in=PAYING).count()
    )


def churn(days: int = 30) -> dict:
    since = timezone.now() - timedelta(days=days)
    canceled = Subscription.objects.filter(
        status__in=[SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED], ended_at__gte=since
    ).count()
    active = Subscription.objects.filter(status__in=RECURRING).count()
    denom = canceled + active
    return {"canceled": canceled, "active": active, "rate": round(canceled / denom * 100, 2) if denom else 0.0}


def conversion_rate(days: int = 30) -> dict:
    since = timezone.now() - timedelta(days=days)
    trials = Subscription.objects.filter(trial_end__isnull=False, created_at__gte=since).count()
    converted = Subscription.objects.filter(
        trial_end__isnull=False, status__in=RECURRING, created_at__gte=since
    ).count()
    return {
        "trials_started": trials,
        "converted": converted,
        "rate": round(converted / trials * 100, 2) if trials else 0.0,
    }


def revenue_by_plan() -> list:
    """Recognised revenue (paid invoices) grouped by plan."""
    data: dict = {}
    qs = Invoice.objects.filter(status=Invoice.Status.PAID).select_related(
        "subscription__plan", "institution_subscription__plan"
    )
    for inv in qs:
        plan = None
        if inv.subscription_id and inv.subscription:
            plan = inv.subscription.plan
        elif inv.institution_subscription_id and inv.institution_subscription:
            plan = inv.institution_subscription.plan
        if plan is None:
            continue
        entry = data.setdefault(plan.id, {"plan": plan.name, "tier": plan.tier, "revenue": ZERO, "invoices": 0})
        entry["revenue"] += inv.amount_paid
        entry["invoices"] += 1
    out = sorted(data.values(), key=lambda x: x["revenue"], reverse=True)
    for entry in out:
        entry["revenue"] = str(entry["revenue"].quantize(Decimal("0.01")))
    return out


def revenue_collected(days: int = 30) -> dict:
    since = timezone.now() - timedelta(days=days)
    agg = Payment.objects.filter(
        status__in=[Payment.Status.SUCCEEDED, Payment.Status.PARTIALLY_REFUNDED],
        created_at__gte=since,
    ).aggregate(gross=Sum("amount"), refunded=Sum("amount_refunded"), n=Count("id"))
    return {
        "gross": str((agg["gross"] or ZERO).quantize(Decimal("0.01"))),
        "refunded": str((agg["refunded"] or ZERO).quantize(Decimal("0.01"))),
        "n": agg["n"] or 0,
    }


def overview() -> dict:
    """One-call dashboard payload for the revenue analytics endpoint."""
    return {
        "active_subscribers": active_subscriber_count(),
        "mrr": str(mrr()),
        "arr": str(arr()),
        "churn": churn(),
        "conversion": conversion_rate(),
        "revenue_by_plan": revenue_by_plan(),
        "revenue_collected": revenue_collected(),
        "currency": getattr(settings, "BILLING_DEFAULT_CURRENCY", "NPR"),
        "generated_at": timezone.now().isoformat(),
    }
