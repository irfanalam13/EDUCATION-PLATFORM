"""Periodic billing jobs (Celery).

``process_subscription_renewals`` runs daily (see CELERY_BEAT_SCHEDULE) and
settles subscriptions whose paid period or trial has elapsed:

  * Provider-managed recurring subscriptions (a non-manual gateway has charged
    the customer out of band) roll forward to the next period.
  * Everyone else — wallet/manual one-off payments, or subs flagged to cancel at
    period end — lapses back to Free.

Auto-charging a stored card from the worker is out of scope here; gateway-side
recurring billing handles that and we reconcile via webhooks + this sweep.
"""
from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from . import services
from .models import Gateway, Subscription, SubscriptionStatus

log = logging.getLogger("apps.billing")


@shared_task
def process_subscription_renewals() -> dict:
    now = timezone.now()
    due = (
        Subscription.objects.filter(
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING],
            current_period_end__lt=now,
        )
        .select_related("plan")
    )
    renewed = expired = 0
    for sub in due.iterator():
        provider_managed = (
            sub.gateway != Gateway.MANUAL
            and sub.gateway_subscription_id
            and not sub.cancel_at_period_end
            and sub.status == SubscriptionStatus.ACTIVE
        )
        if provider_managed:
            services.renew_subscription(sub)
            renewed += 1
        elif services.expire_if_lapsed(sub):
            expired += 1
    log.info("process_subscription_renewals: %s renewed, %s expired", renewed, expired)
    return {"renewed": renewed, "expired": expired}
