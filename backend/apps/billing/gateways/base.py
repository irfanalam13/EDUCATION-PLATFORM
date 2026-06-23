"""Payment gateway abstraction.

Every gateway returns these plain dataclasses so the rest of the billing code is
provider-agnostic. Concrete gateways live alongside this module and register in
``gateways/__init__.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


class GatewayError(Exception):
    """Raised for configuration, network, or provider-side failures."""


class WebhookVerificationError(Exception):
    """Raised when an inbound webhook fails signature/authenticity checks."""


@dataclass
class CheckoutSession:
    """Result of starting a hosted checkout."""

    gateway: str
    reference: str
    redirect_url: str = ""
    client_payload: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookResult:
    """Authenticated, parsed webhook."""

    gateway: str
    event_id: str
    event_type: str
    verified: bool
    payment_reference: str
    amount: Decimal | None
    currency: str
    succeeded: bool
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaymentResult:
    """Result of a server-side verify / refund."""

    gateway: str
    reference: str
    succeeded: bool
    amount: Decimal | None
    currency: str
    status: str
    raw: dict[str, Any] = field(default_factory=dict)


class PaymentGateway:
    """Interface every concrete gateway implements."""

    name: str = ""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def create_checkout(
        self,
        *,
        amount: Decimal,
        currency: str,
        reference: str,
        description: str = "",
        customer_email: str = "",
        success_url: str = "",
        cancel_url: str = "",
        metadata: dict | None = None,
    ) -> CheckoutSession:
        raise NotImplementedError

    def verify_webhook(self, *, body: bytes, headers: dict) -> WebhookResult:
        raise NotImplementedError

    def verify_payment(self, *, reference: str, **kwargs) -> PaymentResult:
        raise NotImplementedError

    def refund(self, *, reference: str, amount: Decimal | None = None, currency: str = "") -> PaymentResult:
        raise NotImplementedError
