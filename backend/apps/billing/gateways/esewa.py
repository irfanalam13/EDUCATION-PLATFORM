"""eSewa gateway (Nepal).

eSewa ePay v2 signs requests/responses with HMAC-SHA256 over a comma-joined
``field=value`` message in ``signed_field_names`` order, base64-encoded. We
verify the response signature on callbacks and offer a server-side status check.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
from decimal import Decimal

from django.conf import settings

from .base import (
    CheckoutSession,
    GatewayError,
    PaymentGateway,
    PaymentResult,
    WebhookResult,
    WebhookVerificationError,
)

LIVE_FORM = "https://epay.esewa.com.np/api/epay/main/v2/form"
SANDBOX_FORM = "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
LIVE_STATUS = "https://epay.esewa.com.np/api/epay/transaction/status/"
SANDBOX_STATUS = "https://rc.esewa.com.np/api/epay/transaction/status/"


class EsewaGateway(PaymentGateway):
    name = "ESEWA"

    @property
    def secret_key(self) -> str:
        return self.config.get("secret_key") or getattr(settings, "ESEWA_SECRET_KEY", "")

    @property
    def product_code(self) -> str:
        return self.config.get("product_code") or getattr(settings, "ESEWA_PRODUCT_CODE", "EPAYTEST")

    @property
    def sandbox(self) -> bool:
        return self.config.get("sandbox", getattr(settings, "ESEWA_SANDBOX", True))

    def _sign(self, message: str) -> str:
        if not self.secret_key:
            raise GatewayError("ESEWA_SECRET_KEY is not configured.")
        digest = hmac.new(self.secret_key.encode(), message.encode(), hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    def create_checkout(
        self, *, amount, currency="NPR", reference="", success_url="https://example.com/success",
        cancel_url="https://example.com/failure", **kwargs,
    ) -> CheckoutSession:
        total = f"{Decimal(amount):.2f}"
        signed_fields = "total_amount,transaction_uuid,product_code"
        message = f"total_amount={total},transaction_uuid={reference},product_code={self.product_code}"
        signature = self._sign(message)
        payload = {
            "amount": total,
            "tax_amount": "0",
            "total_amount": total,
            "transaction_uuid": reference,
            "product_code": self.product_code,
            "product_service_charge": "0",
            "product_delivery_charge": "0",
            "success_url": success_url or "https://example.com/success",
            "failure_url": cancel_url or "https://example.com/failure",
            "signed_field_names": signed_fields,
            "signature": signature,
        }
        return CheckoutSession(
            gateway=self.name,
            reference=reference,
            redirect_url=SANDBOX_FORM if self.sandbox else LIVE_FORM,
            client_payload=payload,
        )

    def verify_webhook(self, *, body: bytes, headers: dict) -> WebhookResult:
        try:
            data = json.loads(body.decode("utf-8"))
        except (ValueError, AttributeError):
            raise WebhookVerificationError("Invalid eSewa payload.")
        self._verify_response_signature(data)
        status = data.get("status", "")
        total = str(data.get("total_amount", "0")).replace(",", "")
        ref = data.get("transaction_uuid", "")
        return WebhookResult(
            gateway=self.name,
            event_id=str(data.get("transaction_code") or ref),
            event_type="esewa.callback",
            verified=True,
            payment_reference=str(ref),
            amount=Decimal(total) if total else None,
            currency="NPR",
            succeeded=status == "COMPLETE",
            raw=data,
        )

    def _verify_response_signature(self, data: dict) -> None:
        signed = data.get("signed_field_names")
        provided = data.get("signature")
        if not signed or not provided:
            raise WebhookVerificationError("Missing eSewa signature fields.")
        message = ",".join(f"{name}={data.get(name)}" for name in signed.split(","))
        if not hmac.compare_digest(self._sign(message), provided):
            raise WebhookVerificationError("eSewa signature mismatch.")

    def verify_payment(self, *, reference, total_amount=None, **kwargs) -> PaymentResult:
        """Server-side status check by transaction_uuid (defence in depth)."""
        import httpx

        base = SANDBOX_STATUS if self.sandbox else LIVE_STATUS
        resp = httpx.get(
            base,
            params={
                "product_code": self.product_code,
                "transaction_uuid": reference,
                "total_amount": total_amount or "",
            },
            timeout=30,
        )
        if resp.status_code >= 400:
            raise GatewayError(f"eSewa status error {resp.status_code}: {resp.text}")
        data = resp.json()
        return PaymentResult(
            gateway=self.name,
            reference=str(reference),
            succeeded=data.get("status") == "COMPLETE",
            amount=Decimal(str(data.get("total_amount", "0"))),
            currency="NPR",
            status=str(data.get("status", "")),
            raw=data,
        )

    def refund(self, *, reference, amount=None, currency="NPR") -> PaymentResult:
        # eSewa has no programmatic refund API; flag for the merchant portal.
        return PaymentResult(
            gateway=self.name, reference=str(reference), succeeded=False,
            amount=amount, currency=currency, status="manual_refund_required",
            raw={"note": "Refund eSewa payments from the merchant portal."},
        )
