"""DRF permission for feature gating.

``requires_feature(KEY)`` builds a permission class that allows the request only
if the user is entitled to that feature (via plan tier or an explicit
FeatureAccess grant), otherwise raises HTTP 402 Payment Required. Pair it with
``IsAuthenticated`` (listed first) so anonymous users get 401/403, not 402.
"""
from __future__ import annotations

from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission

from . import entitlements


class PaymentRequired(APIException):
    status_code = 402
    default_detail = "This feature requires an upgraded plan."
    default_code = "payment_required"


class RequiresFeature(BasePermission):
    """Gate a view behind a billing feature. Set the key via the ``feature``
    attribute (use the ``requires_feature`` factory) or a view-level
    ``required_feature`` attribute."""

    feature: str | None = None

    def has_permission(self, request, view) -> bool:
        feature = getattr(view, "required_feature", None) or self.feature
        if not feature:
            return True
        # Let IsAuthenticated own the anonymous case (401/403, not 402).
        if not (request.user and request.user.is_authenticated):
            return False
        if entitlements.has_feature(request.user, feature):
            return True
        raise PaymentRequired("Upgrade your plan to use this feature.")


def requires_feature(feature_key: str):
    """Build a RequiresFeature permission class bound to a feature key."""
    return type(f"RequiresFeature_{feature_key}", (RequiresFeature,), {"feature": feature_key})
