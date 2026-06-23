"""Create or update the canonical subscription plans."""
from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.billing import features as feat
from apps.billing.models import BillingInterval, Plan

PLANS = [
    {
        "slug": "free",
        "name": "Free",
        "tier": Plan.Tier.FREE,
        "price": Decimal("0.00"),
        "interval": BillingInterval.MONTH,
        "description": "Get started with core learning tools.",
        "trial_days": 0,
        "display_order": 0,
        "feature_list": ["Limited quizzes (10/month)", "Basic progress tracking"],
    },
    {
        "slug": "premium-monthly",
        "name": "Premium Monthly",
        "tier": Plan.Tier.PREMIUM,
        "price": Decimal("499.00"),
        "interval": BillingInterval.MONTH,
        "description": "Unlock the full AI study experience.",
        "trial_days": 14,
        "highlight": True,
        "display_order": 1,
    },
    {
        "slug": "premium-yearly",
        "name": "Premium Yearly",
        "tier": Plan.Tier.PREMIUM,
        "price": Decimal("4990.00"),
        "interval": BillingInterval.YEAR,
        "description": "Premium, billed yearly — two months free.",
        "trial_days": 0,
        "display_order": 2,
        "feature_list": ["Everything in Premium", "2 months free vs monthly"],
    },
    {
        "slug": "institution",
        "name": "Institution",
        "tier": Plan.Tier.INSTITUTION,
        "price": Decimal("299.00"),  # per seat / month
        "interval": BillingInterval.MONTH,
        "description": "Per-seat licensing for schools and colleges.",
        "trial_days": 0,
        "max_seats": 1000,
        "display_order": 3,
    },
]


class Command(BaseCommand):
    help = "Create or update the canonical subscription plans."

    def handle(self, *args, **options):
        created_n = updated_n = 0
        for spec in PLANS:
            slug = spec["slug"]
            defaults = {k: v for k, v in spec.items() if k != "slug"}
            defaults.setdefault("feature_list", list(feat.features_for_tier(spec["tier"]).keys()))
            _, created = Plan.objects.update_or_create(slug=slug, defaults=defaults)
            if created:
                created_n += 1
            else:
                updated_n += 1
            grants = ", ".join(feat.features_for_tier(spec["tier"]).keys())
            self.stdout.write(f"  {spec['name']} ({slug}) -> {grants}")
        self.stdout.write(
            self.style.SUCCESS(f"Plans seeded: {created_n} created, {updated_n} updated.")
        )
