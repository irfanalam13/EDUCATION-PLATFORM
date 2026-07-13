"""Billing orchestration: subscribe / activate / cancel / renew / refund, invoice
creation, feature provisioning, and webhook handling. This is the only module
that mutates subscription lifecycle state, so the rules live in one place.
"""
from __future__ import annotations

import calendar
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .features import features_for_tier
from .gateways import get_gateway
from .models import (
    BillingInterval,
    Coupon,
    FeatureAccess,
    Gateway,
    InstitutionSubscription,
    Invoice,
    Payment,
    Plan,
    Subscription,
    SubscriptionStatus,
    WebhookEvent,
    ZERO,
)

log = logging.getLogger("apps.billing")

_LIVE_STATUSES = [
    SubscriptionStatus.ACTIVE,
    SubscriptionStatus.TRIALING,
    SubscriptionStatus.PAST_DUE,
    SubscriptionStatus.INCOMPLETE,
]


# --------------------------------------------------------------------------- #
# Period maths
# --------------------------------------------------------------------------- #
def period_end_from(start, interval):
    if interval == BillingInterval.YEAR:
        try:
            return start.replace(year=start.year + 1)
        except ValueError:  # Feb 29 -> Feb 28
            return start.replace(year=start.year + 1, day=28)
    if interval == BillingInterval.LIFETIME:
        return None  # no expiry
    month = start.month + 1
    year = start.year
    if month > 12:
        month, year = 1, year + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return start.replace(year=year, month=month, day=day)


# --------------------------------------------------------------------------- #
# Feature provisioning
# --------------------------------------------------------------------------- #
def provision_features(*, user=None, institution=None, tier, source=FeatureAccess.Source.PLAN):
    if user is None and institution is None:
        raise ValueError("provision_features requires a user or institution owner.")
    wanted = features_for_tier(tier)
    period_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for feature, limit in wanted.items():
        FeatureAccess.objects.update_or_create(
            user=user,
            institution=institution,
            feature=feature,
            defaults={
                "is_enabled": True,
                "limit": limit,
                "source": source,
                "expires_at": None,
                "period_start": period_start,
            },
        )
    # Disable anything the new tier no longer grants.
    owner = {"user": user} if user is not None else {"institution": institution}
    FeatureAccess.objects.filter(**owner).exclude(feature__in=wanted.keys()).update(is_enabled=False)


def deprovision_features(*, user=None, institution=None):
    """Drop the owner back to the Free baseline."""
    free_features = features_for_tier(Plan.Tier.FREE)
    owner = {"user": user} if user is not None else {"institution": institution}
    FeatureAccess.objects.filter(**owner).exclude(feature__in=free_features.keys()).update(
        is_enabled=False
    )
    if user is not None:
        provision_features(user=user, tier=Plan.Tier.FREE, source=FeatureAccess.Source.PLAN)
    elif institution is not None:
        FeatureAccess.objects.filter(institution=institution).update(is_enabled=False)


# --------------------------------------------------------------------------- #
# Pricing & invoices
# --------------------------------------------------------------------------- #
@dataclass
class PriceQuote:
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    currency: str
    coupon: "Coupon | None" = None


def quote(plan, coupon=None, seats: int = 1) -> PriceQuote:
    seats = max(1, seats)
    subtotal = max(plan.price * seats, ZERO).quantize(Decimal("0.01"))
    discount = ZERO
    if coupon is not None and coupon.is_valid(plan):
        discount = coupon.discount_for(subtotal)
    total = max(ZERO, subtotal - discount)
    return PriceQuote(
        subtotal=subtotal,
        discount=discount,
        tax=ZERO,
        total=total,
        currency=plan.currency,
        coupon=coupon if discount > ZERO else None,
    )


def create_invoice(*, user=None, subscription=None, institution_subscription=None, q: PriceQuote, plan, coupon=None):
    status = Invoice.Status.PAID if q.total <= ZERO else Invoice.Status.OPEN
    return Invoice.objects.create(
        user=user,
        subscription=subscription,
        institution_subscription=institution_subscription,
        status=status,
        currency=q.currency,
        subtotal=q.subtotal,
        discount_amount=q.discount,
        tax_amount=q.tax,
        total=q.total,
        coupon=coupon,
        issued_at=timezone.now(),
        line_items=[{"name": plan.name, "amount": str(q.subtotal)}],
    )


def mark_invoice_paid(invoice, amount=None):
    invoice.amount_paid = amount if amount is not None else invoice.total
    invoice.status = Invoice.Status.PAID
    invoice.paid_at = timezone.now()
    invoice.save(update_fields=["amount_paid", "status", "paid_at", "updated_at"])


def record_payment(*, invoice, gateway, gateway_payment_id, amount, currency, status=Payment.Status.SUCCEEDED, raw=None, user=None, method=""):
    """Create/Update a Payment idempotently keyed on (gateway, gateway_payment_id)."""
    payment, _ = Payment.objects.update_or_create(
        gateway=gateway,
        gateway_payment_id=gateway_payment_id,
        defaults={
            "invoice": invoice,
            "amount": amount,
            "currency": currency,
            "status": status,
            "raw_payload": raw or {},
            "processed_at": timezone.now(),
            "user": user or (invoice.user if invoice else None),
            "method": method,
        },
    )
    return payment


# --------------------------------------------------------------------------- #
# Subscribe (individual)
# --------------------------------------------------------------------------- #
@dataclass
class SubscribeResult:
    subscription: "Subscription"
    invoice: "Invoice | None"
    requires_payment: bool
    checkout_url: str = ""
    checkout_payload: "dict[str, Any] | None" = field(default_factory=dict)


@transaction.atomic
def subscribe(user, plan, *, gateway=Gateway.MANUAL, coupon_code="", start_trial=True, success_url="", cancel_url=""):
    now = timezone.now()
    coupon = _resolve_coupon(coupon_code, plan)
    _terminate_live_subscriptions(user)

    sub = Subscription(user=user, plan=plan, gateway=gateway, coupon=coupon)

    if plan.is_free:
        sub.status = SubscriptionStatus.ACTIVE
        sub.started_at = now
        sub.current_period_start = now
        sub.current_period_end = period_end_from(now, plan.interval)
        sub.save()
        provision_features(user=user, tier=plan.tier, source=FeatureAccess.Source.PLAN)
        return SubscribeResult(subscription=sub, invoice=None, requires_payment=False)

    if plan.trial_days and start_trial and not _has_used_trial(user):
        sub.status = SubscriptionStatus.TRIALING
        sub.started_at = now
        sub.trial_end = now + timedelta(days=plan.trial_days)
        sub.current_period_end = sub.trial_end
        sub.save()
        provision_features(user=user, tier=plan.tier, source=FeatureAccess.Source.TRIAL)
        return SubscribeResult(subscription=sub, invoice=None, requires_payment=False)

    # Paid, no trial: stay INCOMPLETE until payment clears.
    sub.status = SubscriptionStatus.INCOMPLETE
    sub.save()
    q = quote(plan, coupon)
    invoice = create_invoice(user=user, subscription=sub, q=q, plan=plan, coupon=coupon)
    result = SubscribeResult(subscription=sub, invoice=invoice, requires_payment=True)

    if gateway != Gateway.MANUAL:
        gw = get_gateway(gateway)
        checkout = gw.create_checkout(
            amount=q.total,
            currency=q.currency,
            reference=invoice.number,
            description=plan.name,
            customer_email=getattr(user, "email", ""),
            success_url=success_url,
            cancel_url=cancel_url,
        )
        sub.gateway_subscription_id = checkout.reference
        sub.save(update_fields=["gateway_subscription_id"])
        invoice.gateway_invoice_id = checkout.reference
        invoice.save(update_fields=["gateway_invoice_id"])
        result.checkout_url = checkout.redirect_url
        result.checkout_payload = checkout.client_payload
    return result


def activate_subscription(sub, *, invoice=None, amount=None):
    """Transition a subscription to ACTIVE and provision features."""
    now = timezone.now()
    sub.current_period_start = now
    sub.current_period_end = period_end_from(now, sub.plan.interval)
    sub.status = SubscriptionStatus.ACTIVE
    sub.started_at = sub.started_at or now
    sub.save()
    if invoice is not None and invoice.status != Invoice.Status.PAID:
        mark_invoice_paid(invoice, amount)
    provision_features(user=sub.user, tier=sub.plan.tier, source=FeatureAccess.Source.PLAN)
    log.info("Subscription %s activated (plan=%s)", sub.id, sub.plan_id)
    return sub


def cancel_subscription(sub, *, at_period_end=False):
    now = timezone.now()
    if at_period_end:
        sub.cancel_at_period_end = True
        sub.canceled_at = now
        sub.save()
    else:
        sub.status = SubscriptionStatus.CANCELED
        sub.canceled_at = now
        sub.ended_at = now
        sub.save()
        deprovision_features(user=sub.user)
    _cancel_gateway_subscription(sub)
    log.info("Subscription %s canceled (at_period_end=%s)", sub.id, at_period_end)
    return sub


def renew_subscription(sub):
    """Roll the period forward (called by the renewals task on success)."""
    now = timezone.now()
    if sub.cancel_at_period_end:
        sub.status = SubscriptionStatus.CANCELED
        sub.ended_at = now
        sub.save()
        deprovision_features(user=sub.user)
        return None
    sub.current_period_start = sub.current_period_end or now
    sub.current_period_end = period_end_from(sub.current_period_start, sub.plan.interval)
    sub.status = SubscriptionStatus.ACTIVE
    sub.save()
    # ONCE coupons only discount the first cycle.
    coupon = sub.coupon if (sub.coupon and sub.coupon.duration != Coupon.Duration.ONCE) else None
    q = quote(sub.plan, coupon)
    return create_invoice(user=sub.user, subscription=sub, q=q, plan=sub.plan, coupon=coupon)


def expire_if_lapsed(sub) -> bool:
    """Mark a subscription EXPIRED if its paid period has elapsed. Returns True if changed."""
    now = timezone.now()
    if sub.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING):
        if sub.current_period_end and sub.current_period_end < now:
            sub.status = SubscriptionStatus.CANCELED if sub.cancel_at_period_end else SubscriptionStatus.EXPIRED
            sub.ended_at = now
            sub.save()
            deprovision_features(user=sub.user)
            return True
    return False


def refund_payment(payment, *, amount=None, also_cancel=False):
    """Refund a captured payment (full or partial) and optionally end the sub."""
    gw = get_gateway(payment.gateway)
    refund_amount = amount if amount is not None else (payment.amount - payment.amount_refunded)
    res = gw.refund(reference=payment.gateway_payment_id, amount=refund_amount, currency=payment.currency)
    payment.amount_refunded = min(payment.amount, payment.amount_refunded + refund_amount)
    payment.status = (
        Payment.Status.REFUNDED
        if payment.amount_refunded >= payment.amount
        else Payment.Status.PARTIALLY_REFUNDED
    )
    payment.raw_payload = {**(payment.raw_payload or {}), "refund": res.raw}
    payment.save(update_fields=["amount_refunded", "status", "raw_payload", "updated_at"])

    invoice = payment.invoice
    if invoice and payment.status == Payment.Status.REFUNDED:
        invoice.status = Invoice.Status.REFUNDED
        invoice.save(update_fields=["status", "updated_at"])
    if also_cancel and invoice and invoice.subscription_id:
        cancel_subscription(invoice.subscription)
    log.info("Payment %s refunded amount=%s", payment.id, refund_amount)
    return payment


# --------------------------------------------------------------------------- #
# Subscribe (institution, per-seat)
# --------------------------------------------------------------------------- #
@transaction.atomic
def subscribe_institution(*, institution, plan, seats=1, gateway=Gateway.MANUAL, coupon_code="", billing_email="", purchased_by=None, success_url="", cancel_url=""):
    now = timezone.now()
    coupon = _resolve_coupon(coupon_code, plan)
    seats = max(1, seats)
    if plan.max_seats:
        seats = min(seats, plan.max_seats)

    isub, _ = InstitutionSubscription.objects.update_or_create(
        institution=institution,
        defaults={
            "plan": plan,
            "seats": seats,
            "gateway": gateway,
            "billing_email": billing_email,
            "purchased_by": purchased_by,
            "coupon": coupon,
            "status": SubscriptionStatus.INCOMPLETE,
        },
    )

    if plan.is_free:
        isub.status = SubscriptionStatus.ACTIVE
        isub.current_period_start = now
        isub.current_period_end = period_end_from(now, plan.interval)
        isub.save()
        provision_features(institution=institution, tier=plan.tier, source=FeatureAccess.Source.PLAN)
        return SubscribeResult(subscription=isub, invoice=None, requires_payment=False)

    q = quote(plan, coupon, seats=seats)
    invoice = create_invoice(institution_subscription=isub, q=q, plan=plan, coupon=coupon)
    invoice.line_items = [{"name": f"{plan.name} x{seats} seats", "amount": str(q.subtotal)}]
    invoice.save(update_fields=["line_items"])
    result = SubscribeResult(subscription=isub, invoice=invoice, requires_payment=True)

    if gateway != Gateway.MANUAL:
        gw = get_gateway(gateway)
        checkout = gw.create_checkout(
            amount=q.total, currency=q.currency, reference=invoice.number,
            description=plan.name, customer_email=billing_email,
            success_url=success_url, cancel_url=cancel_url,
        )
        isub.gateway_subscription_id = checkout.reference
        isub.save(update_fields=["gateway_subscription_id"])
        result.checkout_url = checkout.redirect_url
        result.checkout_payload = checkout.client_payload
    return result


def activate_institution_subscription(isub, *, invoice=None, amount=None):
    now = timezone.now()
    isub.current_period_start = now
    isub.current_period_end = period_end_from(now, isub.plan.interval)
    isub.status = SubscriptionStatus.ACTIVE
    isub.save()
    if invoice is not None and invoice.status != Invoice.Status.PAID:
        mark_invoice_paid(invoice, amount)
    provision_features(institution=isub.institution, tier=isub.plan.tier, source=FeatureAccess.Source.PLAN)
    return isub


# --------------------------------------------------------------------------- #
# Webhooks
# --------------------------------------------------------------------------- #
def handle_webhook(gateway_name, body: bytes, headers: dict) -> dict:
    gw = get_gateway(gateway_name)
    result = gw.verify_webhook(body=body, headers=headers)  # raises WebhookVerificationError

    event_id = result.event_id or f"noid-{timezone.now().timestamp()}"
    event, created = WebhookEvent.objects.get_or_create(
        gateway=result.gateway,
        event_id=event_id,
        defaults={
            "event_type": result.event_type,
            "signature_verified": result.verified,
            "payload": result.raw,
        },
    )
    if not created and event.processed:
        return {"status": "ok", "detail": "duplicate"}

    event.signature_verified = result.verified
    event.event_type = result.event_type
    event.payload = result.raw

    if result.verified and result.succeeded:
        _apply_successful_payment(result)
        event.processed = True
        event.save()
        return {"status": "ok", "detail": "processed"}

    event.save()
    return {"status": "ok", "detail": "ignored"}


def _apply_successful_payment(result) -> str:
    """Match a verified successful payment back to an invoice/subscription."""
    invoice = Invoice.objects.filter(number=result.payment_reference).first()
    amount = result.amount if result.amount is not None else (invoice.total if invoice else ZERO)
    currency = result.currency or "NPR"
    record_payment(
        invoice=invoice,
        gateway=result.gateway,
        gateway_payment_id=result.event_id,
        amount=amount,
        currency=currency,
        raw=result.raw,
    )
    if invoice and invoice.subscription_id:
        activate_subscription(invoice.subscription, invoice=invoice, amount=amount)
        return "subscription_activated"
    if invoice and invoice.institution_subscription_id:
        activate_institution_subscription(invoice.institution_subscription, invoice=invoice, amount=amount)
        return "institution_subscription_activated"
    return "payment_recorded_unmatched"


# --------------------------------------------------------------------------- #
# Coupons & helpers
# --------------------------------------------------------------------------- #
def _resolve_coupon(code, plan):
    if not code:
        return None
    coupon = Coupon.objects.filter(code=code.strip()).first()
    if coupon and coupon.is_valid(plan):
        return coupon
    return None


def redeem_coupon(coupon):
    from django.db.models import F

    Coupon.objects.filter(pk=coupon.pk).update(redeemed_count=F("redeemed_count") + 1)


def _terminate_live_subscriptions(user):
    now = timezone.now()
    Subscription.objects.filter(user=user, status__in=_LIVE_STATUSES).update(
        status=SubscriptionStatus.CANCELED, canceled_at=now, ended_at=now
    )


def _has_used_trial(user) -> bool:
    return Subscription.objects.filter(user=user, trial_end__isnull=False).exists()


def _cancel_gateway_subscription(sub):
    # Provider-side cancellation is best-effort; MANUAL is a no-op.
    if sub.gateway == Gateway.MANUAL or not sub.gateway_subscription_id:
        return
    try:  # pragma: no cover - network path
        get_gateway(sub.gateway)
    except Exception:  # noqa: BLE001
        log.warning("Could not cancel gateway subscription for %s", sub.id)
