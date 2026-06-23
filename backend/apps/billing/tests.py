from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.institutions.models import Institution, InstitutionMember

from . import analytics, entitlements, services
from . import features as feat
from .gateways import get_gateway
from .gateways.base import WebhookVerificationError
from .models import (
    BillingInterval,
    Coupon,
    FeatureAccess,
    Gateway,
    InstitutionSubscription,
    Invoice,
    Payment,
    Plan,
    Subscription,
    SubscriptionStatus,
)

User = get_user_model()


def make_plans():
    free = Plan.objects.create(
        tier=Plan.Tier.FREE, name="Free", slug="free", price=Decimal("0.00"),
        interval=BillingInterval.MONTH,
    )
    premium = Plan.objects.create(
        tier=Plan.Tier.PREMIUM, name="Premium", slug="premium-monthly", price=Decimal("499.00"),
        interval=BillingInterval.MONTH, trial_days=14,
    )
    premium_yr = Plan.objects.create(
        tier=Plan.Tier.PREMIUM, name="Premium Yearly", slug="premium-yearly", price=Decimal("4990.00"),
        interval=BillingInterval.YEAR, trial_days=0,
    )
    inst_plan = Plan.objects.create(
        tier=Plan.Tier.INSTITUTION, name="Institution", slug="institution", price=Decimal("299.00"),
        interval=BillingInterval.MONTH, max_seats=1000,
    )
    return free, premium, premium_yr, inst_plan


class BillingTestBase(APITestCase):
    def setUp(self):
        self.free, self.premium, self.premium_yr, self.inst_plan = make_plans()
        self.user = User.objects.create_user("alice", "a@x.com", "x")
        self.client.force_authenticate(self.user)


class PlanApiTests(BillingTestBase):
    def test_plans_public_and_list_features(self):
        self.client.force_authenticate(None)  # public endpoint
        resp = self.client.get(reverse("billing-plans"))
        self.assertEqual(resp.status_code, 200)
        premium = next(p for p in resp.data if p["slug"] == "premium-monthly")
        keys = {f["key"] for f in premium["features"]}
        self.assertIn(feat.FEATURE_AI_TUTOR, keys)


class SubscribeTests(BillingTestBase):
    def test_subscribe_free_activates_immediately(self):
        resp = self.client.post(reverse("billing-subscribe"), {"plan": "free"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], SubscriptionStatus.ACTIVE)
        self.assertFalse(resp.data["requires_payment"])

    def test_subscribe_premium_starts_trial(self):
        resp = self.client.post(reverse("billing-subscribe"), {"plan": "premium-monthly"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], SubscriptionStatus.TRIALING)
        self.assertTrue(entitlements.has_feature(self.user, feat.FEATURE_AI_TUTOR))

    def test_subscribe_paid_no_trial_requires_payment_and_invoice(self):
        resp = self.client.post(
            reverse("billing-subscribe"),
            {"plan": "premium-yearly", "gateway": "MANUAL"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data["requires_payment"])
        self.assertEqual(resp.data["status"], SubscriptionStatus.INCOMPLETE)
        self.assertIsNotNone(resp.data.get("invoice"))
        self.assertEqual(Invoice.objects.filter(user=self.user).count(), 1)
        self.assertFalse(entitlements.has_feature(self.user, feat.FEATURE_AI_TUTOR))

    def test_coupon_discounts_invoice(self):
        Coupon.objects.create(code="HALF", percent_off=50)
        resp = self.client.post(
            reverse("billing-subscribe"),
            {"plan": "premium-yearly", "gateway": "MANUAL", "coupon_code": "HALF"},
            format="json",
        )
        self.assertEqual(resp.data["invoice"]["discount_amount"], "2495.00")
        self.assertEqual(resp.data["invoice"]["total"], "2495.00")

    def test_one_live_subscription_replaces_previous(self):
        services.subscribe(self.user, self.premium)
        services.subscribe(self.user, self.free)
        live = Subscription.objects.filter(
            user=self.user, status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
        )
        self.assertEqual(live.count(), 1)


class FeatureGatingTests(BillingTestBase):
    def test_free_user_has_basic_only(self):
        services.subscribe(self.user, self.free)
        self.assertTrue(entitlements.has_feature(self.user, feat.FEATURE_BASIC_PROGRESS))
        self.assertFalse(entitlements.has_feature(self.user, feat.FEATURE_ADVANCED_ANALYTICS))

    def test_free_quiz_quota_is_metered(self):
        services.subscribe(self.user, self.free)
        row = FeatureAccess.objects.get(user=self.user, feature=feat.FEATURE_UNLIMITED_QUIZZES)
        self.assertEqual(row.limit, feat.FREE_MONTHLY_QUIZ_LIMIT)
        for _ in range(feat.FREE_MONTHLY_QUIZ_LIMIT):
            self.assertTrue(entitlements.consume_quota(self.user, feat.FEATURE_UNLIMITED_QUIZZES))
        self.assertFalse(entitlements.consume_quota(self.user, feat.FEATURE_UNLIMITED_QUIZZES))

    def test_premium_quota_unlimited(self):
        services.subscribe(self.user, self.premium)
        services.activate_subscription(self.user.subscriptions.first())
        for _ in range(50):
            self.assertTrue(entitlements.consume_quota(self.user, feat.FEATURE_UNLIMITED_QUIZZES))

    def test_subscription_endpoint_snapshot(self):
        services.subscribe(self.user, self.premium)
        resp = self.client.get(reverse("billing-subscription"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["entitlements"]["tier"], Plan.Tier.PREMIUM)


class CancelTests(BillingTestBase):
    def test_cancel_at_period_end_keeps_access(self):
        services.subscribe(self.user, self.premium)
        sub = self.user.subscriptions.first()
        services.activate_subscription(sub)
        resp = self.client.post(reverse("billing-cancel"), {"at_period_end": True}, format="json")
        self.assertEqual(resp.status_code, 200)
        sub.refresh_from_db()
        self.assertTrue(sub.cancel_at_period_end)
        self.assertEqual(sub.status, SubscriptionStatus.ACTIVE)

    def test_cancel_immediately_revokes(self):
        services.subscribe(self.user, self.premium)
        sub = self.user.subscriptions.first()
        services.activate_subscription(sub)
        services.cancel_subscription(sub)
        sub.refresh_from_db()
        self.assertEqual(sub.status, SubscriptionStatus.CANCELED)
        self.assertFalse(entitlements.has_feature(self.user, feat.FEATURE_AI_TUTOR))


@override_settings(STRIPE_WEBHOOK_SECRET="whsec_test_secret")
class StripeWebhookTests(BillingTestBase):
    SECRET = "whsec_test_secret"

    def _signed_headers(self, body: bytes):
        t = str(int(time.time()))
        sig = hmac.new(self.SECRET.encode(), f"{t}.{body.decode()}".encode(), hashlib.sha256).hexdigest()
        return {"HTTP_STRIPE_SIGNATURE": f"t={t},v1={sig}"}

    def _event(self, event_id, invoice_number):
        return json.dumps(
            {
                "id": event_id,
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "client_reference_id": invoice_number,
                        "amount_total": 499000,
                        "currency": "npr",
                        "payment_status": "paid",
                    }
                },
            }
        ).encode()

    def test_valid_signature_activates_subscription(self):
        result = services.subscribe(self.user, self.premium_yr, gateway=Gateway.MANUAL)
        body = self._event("evt_1", result.invoice.number)
        resp = self.client.post(
            reverse("billing-webhook", args=["stripe"]), data=body,
            content_type="application/json", **self._signed_headers(body),
        )
        self.assertEqual(resp.status_code, 200)
        result.subscription.refresh_from_db()
        self.assertEqual(result.subscription.status, SubscriptionStatus.ACTIVE)
        self.assertTrue(entitlements.has_feature(self.user, feat.FEATURE_AI_TUTOR))

    def test_bad_signature_rejected(self):
        body = self._event("evt_2", "INV-NOPE")
        resp = self.client.post(
            reverse("billing-webhook", args=["stripe"]), data=body,
            content_type="application/json", HTTP_STRIPE_SIGNATURE="t=1,v1=deadbeef",
        )
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_event_is_idempotent(self):
        result = services.subscribe(self.user, self.premium_yr, gateway=Gateway.MANUAL)
        body = self._event("evt_dup", result.invoice.number)
        headers = self._signed_headers(body)
        url = reverse("billing-webhook", args=["stripe"])
        self.client.post(url, data=body, content_type="application/json", **headers)
        resp = self.client.post(url, data=body, content_type="application/json", **headers)
        self.assertEqual(resp.data["detail"], "duplicate")
        self.assertEqual(Payment.objects.filter(gateway=Gateway.STRIPE).count(), 1)


@override_settings(MANUAL_WEBHOOK_TOKEN="tok123")
class ManualWebhookTests(BillingTestBase):
    def test_manual_token_required(self):
        result = services.subscribe(self.user, self.premium_yr, gateway=Gateway.MANUAL)
        body = json.dumps(
            {"event_id": "m1", "reference": result.invoice.number, "amount": "4990.00", "currency": "NPR"}
        ).encode()
        resp = self.client.post(
            reverse("billing-webhook", args=["manual"]), data=body,
            content_type="application/json", HTTP_X_WEBHOOK_TOKEN="tok123",
        )
        self.assertEqual(resp.status_code, 200)
        result.subscription.refresh_from_db()
        self.assertEqual(result.subscription.status, SubscriptionStatus.ACTIVE)


class RefundTests(BillingTestBase):
    def test_refund_marks_payment_and_cancels(self):
        result = services.subscribe(self.user, self.premium_yr, gateway=Gateway.MANUAL)
        services.record_payment(
            invoice=result.invoice, gateway=Gateway.MANUAL, gateway_payment_id="pay_1",
            amount=result.invoice.total, currency="NPR",
        )
        services.activate_subscription(result.subscription, invoice=result.invoice)
        payment = Payment.objects.get(gateway_payment_id="pay_1")

        admin = User.objects.create_user("admin", "admin@x.com", "x", is_staff=True)
        self.client.force_authenticate(admin)
        resp = self.client.post(
            reverse("billing-refund"),
            {"payment_id": payment.id, "cancel_subscription": True},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        payment.refresh_from_db()
        result.subscription.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.REFUNDED)
        self.assertEqual(result.subscription.status, SubscriptionStatus.CANCELED)


class InstitutionSubscriptionTests(BillingTestBase):
    def setUp(self):
        super().setUp()
        self.institution = Institution.objects.create(name="Acme College", slug="acme")
        InstitutionMember.objects.create(
            institution=self.institution, user=self.user,
            role=InstitutionMember.Role.ADMIN, status=InstitutionMember.Status.ACTIVE,
        )

    def test_admin_can_subscribe_institution_with_seats(self):
        resp = self.client.post(
            reverse("billing-subscribe"),
            {"plan": "institution", "institution_id": self.institution.id, "seats": 25, "gateway": "MANUAL"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        isub = InstitutionSubscription.objects.get(institution=self.institution)
        self.assertEqual(isub.seats, 25)
        self.assertEqual(resp.data["invoice"]["total"], "7475.00")

    def test_member_gets_institution_features_after_activation(self):
        services.subscribe_institution(
            institution=self.institution, plan=self.inst_plan, seats=10, gateway=Gateway.MANUAL,
            purchased_by=self.user,
        )
        isub = InstitutionSubscription.objects.get(institution=self.institution)
        services.activate_institution_subscription(isub)
        bob = User.objects.create_user("bob", "bob@x.com", "x")
        InstitutionMember.objects.create(
            institution=self.institution, user=bob,
            role=InstitutionMember.Role.STUDENT, status=InstitutionMember.Status.ACTIVE,
        )
        self.assertTrue(entitlements.has_feature(bob, feat.FEATURE_INSTITUTION_ANALYTICS))
        self.assertEqual(entitlements.effective_tier(bob), Plan.Tier.INSTITUTION)

    def test_non_admin_cannot_subscribe_institution(self):
        evil = User.objects.create_user("evil", "evil@x.com", "x")
        self.client.force_authenticate(evil)
        resp = self.client.post(
            reverse("billing-subscribe"),
            {"plan": "institution", "institution_id": self.institution.id, "gateway": "MANUAL"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)


class RevenueAnalyticsTests(BillingTestBase):
    def test_mrr_arr_and_revenue_by_plan(self):
        u1 = User.objects.create_user("u", "u@x.com", "x")
        services.subscribe(u1, self.premium)
        services.activate_subscription(u1.subscriptions.first())

        u2 = User.objects.create_user("uy", "uy@x.com", "x")
        result = services.subscribe(u2, self.premium_yr, gateway=Gateway.MANUAL)
        services.record_payment(
            invoice=result.invoice, gateway=Gateway.MANUAL, gateway_payment_id="p_y",
            amount=result.invoice.total, currency="NPR",
        )
        services.activate_subscription(result.subscription, invoice=result.invoice)

        expected_mrr = (Decimal("4990.00") / 12).quantize(Decimal("0.01")) + Decimal("499.00")
        self.assertEqual(analytics.mrr(), expected_mrr)
        self.assertEqual(analytics.arr(), (expected_mrr * 12).quantize(Decimal("0.01")))
        plan_names = {row["plan"] for row in analytics.revenue_by_plan()}
        self.assertIn("Premium Yearly", plan_names)

    def test_conversion_and_churn(self):
        c1 = User.objects.create_user("c1", "c1@x.com", "x")
        services.subscribe(c1, self.premium)
        services.activate_subscription(c1.subscriptions.first())
        self.assertEqual(analytics.conversion_rate()["trials_started"], 1)
        self.assertEqual(analytics.conversion_rate()["converted"], 1)
        services.cancel_subscription(c1.subscriptions.first())
        self.assertGreaterEqual(analytics.churn()["canceled"], 1)

    def test_revenue_endpoint_requires_admin(self):
        resp = self.client.get(reverse("billing-revenue"))
        self.assertEqual(resp.status_code, 403)
        radmin = User.objects.create_user("radmin", "r@x.com", "x", is_staff=True)
        self.client.force_authenticate(radmin)
        resp = self.client.get(reverse("billing-revenue"))
        self.assertIn("mrr", resp.data)


class GatewaySignatureUnitTests(BillingTestBase):
    def test_stripe_replay_rejected(self):
        gw = get_gateway("STRIPE", {"webhook_secret": "webhook_secret"})
        old = str(int(time.time()) - 10_000)
        body = b"{}"
        sig = hmac.new(b"webhook_secret", f"{old}.{body.decode()}".encode(), hashlib.sha256).hexdigest()
        with self.assertRaises(WebhookVerificationError):
            gw.verify_webhook(body=body, headers={"Stripe-Signature": f"t={old},v1={sig}"})

    def test_esewa_signature_roundtrip(self):
        gw = get_gateway("ESEWA", {"secret_key": "8gBm/:&EnhH.1/q"})
        data = {
            "transaction_code": "ABC",
            "status": "COMPLETE",
            "total_amount": "100.0",
            "transaction_uuid": "INV-1",
            "product_code": "EPAYTEST",
        }
        signed = "transaction_code,status,total_amount,transaction_uuid,product_code"
        message = ",".join(f"{f}={data[f]}" for f in signed.split(","))
        data["signed_field_names"] = signed
        data["signature"] = gw._sign(message)
        result = gw.verify_webhook(body=json.dumps(data).encode(), headers={})
        self.assertTrue(result.verified)
        self.assertTrue(result.succeeded)
