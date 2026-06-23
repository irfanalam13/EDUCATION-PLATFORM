"""Manual / offline gateway.

The default when no provider keys are configured. Checkout is a no-op (the
operator confirms payment out of band), and the webhook is authenticated with a
shared secret token (``MANUAL_WEBHOOK_TOKEN``) so back-office tools / tests can
mark an invoice paid. Mirrors the AI app's keyless-fallback philosophy.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings

from .base import CheckoutSession, PaymentGateway, PaymentResult, WebhookResult


class ManualGateway(PaymentGateway):
    name = "MANUAL"

    def create_checkout(self, *, amount, currency="NPR", reference="", **kwargs) -> CheckoutSession:
        return CheckoutSession(
            gateway=self.name,
            reference=str(reference),
            redirect_url="",
            client_payload={"instructions": "Manual payment — confirm offline."},
        )

    def verify_webhook(self, *, body: bytes, headers: dict) -> WebhookResult:
        import json

        expected = self.config.get("token") or getattr(settings, "MANUAL_WEBHOOK_TOKEN", "")
        provided = headers.get("X-Webhook-Token") or headers.get("x-webhook-token") or ""
        verified = bool(expected) and provided == expected
        try:
            data = json.loads(body.decode("utf-8"))
        except (ValueError, AttributeError):
            data = {}
        amount = data.get("amount")
        return WebhookResult(
            gateway=self.name,
            event_id=str(data.get("event_id") or data.get("reference") or ""),
            event_type=str(data.get("type") or "manual.payment"),
            verified=verified,
            payment_reference=str(data.get("reference") or ""),
            amount=Decimal(str(amount)) if amount is not None else None,
            currency=str(data.get("currency") or "NPR"),
            succeeded=verified and bool(data.get("succeeded", True)),
            raw=data,
        )

    def verify_payment(self, *, reference, **kwargs) -> PaymentResult:
        return PaymentResult(
            gateway=self.name, reference=str(reference), succeeded=False,
            amount=None, currency="NPR", status="pending", raw={},
        )

    def refund(self, *, reference, amount=None, currency="NPR") -> PaymentResult:
        return PaymentResult(
            gateway=self.name, reference=str(reference), succeeded=True,
            amount=amount, currency=currency, status="refunded", raw={},
        )
