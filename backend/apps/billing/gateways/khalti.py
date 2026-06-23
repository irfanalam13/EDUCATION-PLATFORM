"""Khalti gateway (Nepal).

Khalti ePayment v2: initiate a payment to get a hosted ``payment_url`` + ``pidx``,
then confirm authoritatively via the lookup endpoint. Amounts are in paisa
(NPR * 100). Network calls use ``httpx`` (imported lazily).
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings

from .base import (
    CheckoutSession,
    GatewayError,
    PaymentGateway,
    PaymentResult,
    WebhookResult,
)

LIVE_BASE = "https://khalti.com/api/v2"
SANDBOX_BASE = "https://dev.khalti.com/api/v2"


class KhaltiGateway(PaymentGateway):
    name = "KHALTI"

    @property
    def secret_key(self) -> str:
        return self.config.get("secret_key") or getattr(settings, "KHALTI_SECRET_KEY", "")

    @property
    def base_url(self) -> str:
        sandbox = self.config.get("sandbox", getattr(settings, "KHALTI_SANDBOX", True))
        return SANDBOX_BASE if sandbox else LIVE_BASE

    def _headers(self) -> dict:
        if not self.secret_key:
            raise GatewayError("KHALTI_SECRET_KEY is not configured.")
        return {"Authorization": f"Key {self.secret_key}", "Content-Type": "application/json"}

    def create_checkout(
        self, *, amount, currency="NPR", reference="", description="Subscription",
        customer_email="", success_url="https://example.com/success", **kwargs,
    ) -> CheckoutSession:
        import httpx

        payload = {
            "return_url": success_url or "https://example.com/success",
            "website_url": "https://example.com",
            "amount": int((Decimal(amount) * 100).to_integral_value()),  # paisa
            "purchase_order_id": reference,
            "purchase_order_name": description or "Subscription",
            "customer_info": {"email": customer_email} if customer_email else {},
        }
        resp = httpx.post(
            f"{self.base_url}/epayment/initiate/", json=payload, headers=self._headers(), timeout=30
        )
        if resp.status_code >= 400:
            raise GatewayError(f"Khalti error {resp.status_code}: {resp.text}")
        data = resp.json()
        return CheckoutSession(
            gateway=self.name,
            reference=reference,
            redirect_url=data.get("payment_url", ""),
            client_payload={"pidx": data.get("pidx")},
            raw=data,
        )

    def verify_webhook(self, *, body: bytes, headers: dict) -> WebhookResult:
        import json

        try:
            data = json.loads(body.decode("utf-8"))
        except (ValueError, AttributeError):
            data = {}
        # Khalti callbacks are not signed; treat as a lookup trigger only.
        return WebhookResult(
            gateway=self.name,
            event_id=str(data.get("pidx") or data.get("transaction_id") or ""),
            event_type="khalti.callback",
            verified=False,
            payment_reference=str(data.get("purchase_order_id") or ""),
            amount=None,
            currency="NPR",
            succeeded=False,
            raw=data,
        )

    def verify_payment(self, *, reference, pidx=None, **kwargs) -> PaymentResult:
        """Authoritative confirmation via the lookup endpoint."""
        import httpx

        resp = httpx.post(
            f"{self.base_url}/epayment/lookup/",
            json={"pidx": pidx or reference},
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code >= 400:
            raise GatewayError(f"Khalti lookup error {resp.status_code}: {resp.text}")
        data = resp.json()
        return PaymentResult(
            gateway=self.name,
            reference=str(reference),
            succeeded=data.get("status") == "Completed",
            amount=(Decimal(data.get("total_amount", 0)) / 100).quantize(Decimal("0.01")),
            currency="NPR",
            status=str(data.get("status", "")),
            raw=data,
        )

    def refund(self, *, reference, amount=None, currency="NPR") -> PaymentResult:
        return PaymentResult(
            gateway=self.name, reference=str(reference), succeeded=False,
            amount=amount, currency=currency, status="manual_refund_required",
            raw={"note": "Refund Khalti payments from the merchant dashboard."},
        )
