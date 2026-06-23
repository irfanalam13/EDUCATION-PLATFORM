"""Feature-gate middleware.

Attaches ``request.entitlements`` — a lazy, per-request accessor over the
entitlement helpers — so views/permissions can ask ``request.entitlements.has(
feat.FEATURE_AI_TUTOR)`` or meter quota without re-querying. Does no DB work
itself; everything is computed on first access and cached for the request.
"""
from __future__ import annotations

from . import entitlements


class RequestEntitlements:
    def __init__(self, request):
        self._request = request
        self._feature_cache: dict = {}
        self._tier = None

    @property
    def user(self):
        return getattr(self._request, "user", None)

    @property
    def tier(self):
        if self._tier is None:
            self._tier = entitlements.effective_tier(self.user)
        return self._tier

    def has(self, feature) -> bool:
        if feature not in self._feature_cache:
            self._feature_cache[feature] = entitlements.has_feature(self.user, feature)
        return self._feature_cache[feature]

    def quota_remaining(self, feature):
        return entitlements.quota_remaining(self.user, feature)

    def consume(self, feature, amount: int = 1) -> bool:
        ok = entitlements.consume_quota(self.user, feature, amount)
        self._feature_cache.pop(feature, None)
        return ok

    def snapshot(self):
        return entitlements.snapshot(self.user)


class FeatureGateMiddleware:
    """Lightweight: only wires up ``request.entitlements`` (no DB work itself)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.entitlements = RequestEntitlements(request)
        return self.get_response(request)
