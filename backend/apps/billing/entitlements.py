"""Read-side entitlement resolution.

Answers "what is this user allowed to do?" across their personal subscription
and any institution memberships, plus per-feature quota metering. Pure reads
except ``consume_quota`` which atomically meters usage.
"""
from __future__ import annotations

from django.utils import timezone

from . import features as feat
from .models import (
    FeatureAccess,
    InstitutionSubscription,
    Plan,
    Subscription,
    SubscriptionStatus,
)

_LIVE = [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
_TIER_RANK = {Plan.Tier.FREE: 0, Plan.Tier.PREMIUM: 1, Plan.Tier.INSTITUTION: 2}


def active_subscription(user):
    """The user's current personal subscription, if entitled."""
    if not getattr(user, "is_authenticated", False):
        return None
    sub = (
        Subscription.objects.filter(user=user, status__in=_LIVE)
        .select_related("plan")
        .order_by("-current_period_end")
        .first()
    )
    if sub and sub.is_active:
        return sub
    return None


def institution_ids_for(user):
    """Institutions where the user is an ACTIVE member."""
    if not getattr(user, "is_authenticated", False):
        return []
    from apps.institutions.models import InstitutionMember

    return list(
        InstitutionMember.objects.filter(
            user=user, status=InstitutionMember.Status.ACTIVE
        ).values_list("institution_id", flat=True)
    )


def active_institution_subscriptions(user):
    inst_ids = institution_ids_for(user)
    if not inst_ids:
        return []
    subs = (
        InstitutionSubscription.objects.filter(institution_id__in=inst_ids, status__in=_LIVE)
        .select_related("plan")
    )
    return [s for s in subs if s.is_active]


def effective_tier(user):
    """Highest tier the user is entitled to across personal + institution subs."""
    best = Plan.Tier.FREE
    sub = active_subscription(user)
    if sub:
        best = sub.plan.tier
    for isub in active_institution_subscriptions(user):
        if _TIER_RANK.get(isub.plan.tier, 0) > _TIER_RANK.get(best, 0):
            best = isub.plan.tier
    return best


def _row_is_live(row) -> bool:
    return row.is_live


def models_q_owner(user, inst_ids):
    from django.db.models import Q

    q = Q(user=user)
    if inst_ids:
        q |= Q(institution_id__in=inst_ids)
    return q


def has_feature(user, feature) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    inst_ids = institution_ids_for(user)
    rows = FeatureAccess.objects.filter(models_q_owner(user, inst_ids), feature=feature)
    if any(_row_is_live(r) for r in rows):
        return True
    return feat.tier_grants(effective_tier(user), feature)


def feature_row_for(user, feature):
    """Return the user's personal FeatureAccess row for metering, if any."""
    return FeatureAccess.objects.filter(user=user, feature=feature).first()


def quota_remaining(user, feature):
    """Remaining quota for a metered feature. None == unlimited / not metered."""
    row = feature_row_for(user, feature)
    if row is None:
        return None if feat.tier_grants(effective_tier(user), feature) else 0
    _maybe_reset_period(row)
    return row.remaining


def consume_quota(user, feature, amount: int = 1) -> bool:
    from django.db import transaction
    from django.db.models import F

    with transaction.atomic():
        row = (
            FeatureAccess.objects.select_for_update()
            .filter(user=user, feature=feature)
            .first()
        )
        if row is None:
            # No metering row: allowed iff the tier grants the feature (unlimited).
            return feat.tier_grants(effective_tier(user), feature)
        _maybe_reset_period(row, save=True)
        if row.limit <= 0:
            return True  # unlimited
        if row.used + amount > row.limit:
            return False
        FeatureAccess.objects.filter(pk=row.pk).update(used=F("used") + amount)
        return True


def _maybe_reset_period(row, save: bool = False) -> None:
    """Reset a monthly quota window when the calendar month rolls over."""
    if row.limit <= 0:
        return
    now = timezone.now()
    start = row.period_start
    if start is None or (start.year, start.month) != (now.year, now.month):
        row.period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        row.used = 0
        if save:
            row.save(update_fields=["period_start", "used"])


def snapshot(user) -> dict:
    """Compact entitlement summary for the /subscription endpoint and clients."""
    tier = effective_tier(user)
    inst_ids = institution_ids_for(user)
    rows = list(FeatureAccess.objects.filter(models_q_owner(user, inst_ids)))
    by_feature = {r.feature: r for r in rows if r.is_live}
    out = []
    for key, limit in feat.features_for_tier(tier).items():
        row = by_feature.get(key)
        out.append(
            {
                "key": key,
                "label": feat.FEATURE_LABELS.get(key, key),
                "limit": row.limit if row else limit,
                "used": row.used if row else 0,
                "remaining": row.remaining if row else (None if limit <= 0 else limit),
            }
        )
    return {"tier": str(tier), "features": out}
