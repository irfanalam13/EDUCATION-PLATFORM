"""Seed Free-tier feature access for every new user.

Gated on the existence of a Free plan so the signal is a no-op until billing is
seeded (``manage.py seed_plans``) — this keeps non-billing tests/fixtures that
create users from spuriously creating FeatureAccess rows.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

log = logging.getLogger("apps.billing")


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def seed_free_features(sender, instance, created, **kwargs):
    if not created:
        return
    from . import services
    from .models import Plan

    try:
        if not Plan.objects.filter(tier=Plan.Tier.FREE).exists():
            return
        services.provision_features(user=instance, tier=Plan.Tier.FREE)
    except Exception:  # noqa: BLE001 - never block user creation on billing
        log.exception("Failed to seed free features for user %s", instance.pk)
