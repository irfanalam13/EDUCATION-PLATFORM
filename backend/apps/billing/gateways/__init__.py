"""Gateway registry. ``get_gateway("STRIPE")`` returns a configured instance."""
from __future__ import annotations

from .base import (
    CheckoutSession,
    GatewayError,
    PaymentGateway,
    PaymentResult,
    WebhookResult,
    WebhookVerificationError,
)
from .esewa import EsewaGateway
from .khalti import KhaltiGateway
from .manual import ManualGateway
from .stripe import StripeGateway

_REGISTRY: dict[str, type[PaymentGateway]] = {
    "STRIPE": StripeGateway,
    "KHALTI": KhaltiGateway,
    "ESEWA": EsewaGateway,
    "MANUAL": ManualGateway,
}

SUPPORTED_GATEWAYS = tuple(_REGISTRY.keys())


def get_gateway(name: str, config: dict | None = None) -> PaymentGateway:
    cls = _REGISTRY.get((name or "").upper())
    if cls is None:
        raise GatewayError(f"Unknown payment gateway: {name}")
    return cls(config)


__all__ = [
    "CheckoutSession",
    "GatewayError",
    "PaymentGateway",
    "PaymentResult",
    "WebhookResult",
    "WebhookVerificationError",
    "SUPPORTED_GATEWAYS",
    "get_gateway",
]
