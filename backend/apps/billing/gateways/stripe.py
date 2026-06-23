"""Stripe gateway (international cards).

Talks to Stripe's REST API directly with ``httpx`` (imported lazily so the app
boots without the dependency when Stripe is unused). Webhook authenticity is
verified with the standard ``Stripe-Signature`` HMAC-SHA256 scheme including a
replay-protection timestamp tolerance.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal
from typing import Any

from django.conf import settings

from .base import (
    CheckoutSession,
    GatewayError,
    PaymentGateway,
    PaymentResult,
    WebhookResult,
    WebhookVerificationError,
)

STRIPE_API = "https://api.stripe.com/v1"
# Currencies Stripe treats as zero-decimal (amount is already in major units).
_ZERO_DECIMAL = {"jpy", "krw", "vnd", "clp", "isk"}
_TOLERANCE_SECONDS = 300


def _to_minor(amount: Decimal, currency: str) -> int:
    if currency.lower() in _ZERO_DECIMAL:
        return int(amount.to_integral_value())
    return int((amount * 100).to_integral_value())


def _from_minor(value, currency: str) -> Decimal:
    if currency.lower() in _ZERO_DECIMAL:
        return Decimal(value).quantize(Decimal("0.01"))
    return (Decimal(value) / 100).quantize(Decimal("0.01"))


def _flatten(data: dict, parent: str = "") -> dict:
    """Stripe's form API uses bracketed keys: a[b][c]=v and a[0][b]=v."""
    out: dict[str, Any] = {}
    for key, value in data.items():
        composed = f"{parent}[{key}]" if parent else key
        if isinstance(value, dict):
            out.update(_flatten(value, composed))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    out.update(_flatten(item, f"{composed}[{i}]"))
                else:
                    out[f"{composed}[{i}]"] = item
        else:
            out[composed] = value
    return out


class StripeGateway(PaymentGateway):
    name = "STRIPE"

    @property
    def secret_key(self) -> str:
        return self.config.get("secret_key") or getattr(settings, "STRIPE_SECRET_KEY", "")

    @property
    def webhook_secret(self) -> str:
        return self.config.get("webhook_secret") or getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    def _post(self, path: str, data: dict) -> dict:
        if not self.secret_key:
            raise GatewayError("STRIPE_SECRET_KEY is not configured.")
        import httpx

        resp = httpx.post(
            f"{STRIPE_API}{path}",
            data=_flatten(data),
            auth=(self.secret_key, ""),
            timeout=30,
        )
        if resp.status_code >= 400:
            raise GatewayError(f"Stripe error {resp.status_code}: {resp.text}")
        return resp.json()

    def create_checkout(
        self, *, amount, currency="usd", reference="", description="Subscription",
        customer_email="", success_url="https://example.com/success",
        cancel_url="https://example.com/cancel", metadata=None,
    ) -> CheckoutSession:
        currency = currency.lower()
        payload = {
            "mode": "payment",
            "success_url": success_url or "https://example.com/success",
            "cancel_url": cancel_url or "https://example.com/cancel",
            "client_reference_id": reference,
            "line_items": [
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": currency,
                        "unit_amount": _to_minor(Decimal(amount), currency),
                        "product_data": {"name": description or "Subscription"},
                    },
                }
            ],
        }
        if customer_email:
            payload["customer_email"] = customer_email
        data = self._post("/checkout/sessions", payload)
        return CheckoutSession(
            gateway=self.name,
            reference=reference,
            redirect_url=data.get("url", ""),
            client_payload={"id": data.get("id")},
            raw=data,
        )

    def verify_webhook(self, *, body: bytes, headers: dict) -> WebhookResult:
        sig = headers.get("Stripe-Signature") or headers.get("stripe-signature") or ""
        self._verify_signature(body, sig)
        payload = json.loads(body.decode("utf-8"))
        obj = payload.get("data", {}).get("object", {})
        event_type = payload.get("type", "")
        amount_minor = obj.get("amount_total") or obj.get("amount_received") or 0
        currency = obj.get("currency", "usd")
        return WebhookResult(
            gateway=self.name,
            event_id=str(payload.get("id", "")),
            event_type=event_type,
            verified=True,
            payment_reference=str(obj.get("client_reference_id") or obj.get("id") or ""),
            amount=_from_minor(amount_minor, currency) if amount_minor else None,
            currency=currency.upper(),
            succeeded=obj.get("payment_status") == "paid" or event_type.endswith("payment_intent.succeeded"),
            raw=payload,
        )

    def _verify_signature(self, body: bytes, sig_header: str) -> None:
        if not self.webhook_secret:
            raise WebhookVerificationError("STRIPE_WEBHOOK_SECRET is not configured.")
        if not sig_header:
            raise WebhookVerificationError("Missing Stripe-Signature header.")
        parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
        timestamp = parts.get("t")
        signature = parts.get("v1")
        if not timestamp or not signature:
            raise WebhookVerificationError("Malformed Stripe-Signature header.")
        try:
            if abs(int(time.time()) - int(timestamp)) > _TOLERANCE_SECONDS:
                raise WebhookVerificationError("Stripe webhook timestamp outside tolerance.")
        except ValueError:
            raise WebhookVerificationError("Invalid Stripe timestamp.")
        signed_payload = f"{timestamp}.{body.decode('utf-8')}".encode()
        expected = hmac.new(self.webhook_secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise WebhookVerificationError("Stripe signature mismatch.")

    def verify_payment(self, *, reference, **kwargs) -> PaymentResult:
        if not self.secret_key:
            raise GatewayError("STRIPE_SECRET_KEY is not configured.")
        import httpx

        resp = httpx.get(
            f"{STRIPE_API}/checkout/sessions/{reference}", auth=(self.secret_key, ""), timeout=30
        )
        if resp.status_code >= 400:
            raise GatewayError(f"Stripe error {resp.status_code}: {resp.text}")
        data = resp.json()
        currency = data.get("currency", "usd")
        return PaymentResult(
            gateway=self.name,
            reference=str(reference),
            succeeded=data.get("payment_status") == "paid",
            amount=_from_minor(data.get("amount_total", 0), currency),
            currency=currency.upper(),
            status=data.get("payment_status", ""),
            raw=data,
        )

    def refund(self, *, reference, amount=None, currency="usd") -> PaymentResult:
        payload = {"payment_intent": reference}
        if amount is not None:
            payload["amount"] = _to_minor(Decimal(amount), currency)
        data = self._post("/refunds", payload)
        return PaymentResult(
            gateway=self.name,
            reference=str(reference),
            succeeded=data.get("status") in ("succeeded", "pending"),
            amount=amount,
            currency=currency.upper(),
            status=data.get("status", ""),
            raw=data,
        )
