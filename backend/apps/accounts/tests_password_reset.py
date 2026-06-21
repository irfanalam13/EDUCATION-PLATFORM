"""Phase 3: password reset flow (OTP-based)."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.accounts.models import EmailOTP

User = get_user_model()


# Django's test runner forces DEBUG=False; re-enable it so the dev_otp is
# returned in responses (lets the test read the code without email plumbing).
@override_settings(DEBUG=True)
class PasswordResetFlowTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="reset", email="reset@x.com", password="Old-Pass!234", is_active=True
        )

    def test_full_reset_flow(self):
        # 1) request: returns generic message + dev_otp (DEBUG=True in tests)
        resp = self.client.post(reverse("password-reset"), {"email": "reset@x.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        code = resp.data.get("dev_otp")
        self.assertIsNotNone(code)

        # 2) confirm with code + strong new password
        confirm = self.client.post(
            reverse("password-reset-confirm"),
            {"email": "reset@x.com", "code": code,
             "new_password": "Br4nd-New!pw", "new_password2": "Br4nd-New!pw"},
            format="json",
        )
        self.assertEqual(confirm.status_code, 200, confirm.content)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Br4nd-New!pw"))
        # OTP consumed
        self.assertTrue(
            EmailOTP.objects.filter(user=self.user, purpose=EmailOTP.Purpose.RESET_PASSWORD,
                                    consumed_at__isnull=False).exists()
        )

    def test_unknown_email_is_non_enumerating(self):
        resp = self.client.post(reverse("password-reset"), {"email": "nobody@x.com"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("dev_otp", resp.data)  # no code generated, but same 200

    def test_invalid_code_rejected(self):
        self.client.post(reverse("password-reset"), {"email": "reset@x.com"}, format="json")
        bad = self.client.post(
            reverse("password-reset-confirm"),
            {"email": "reset@x.com", "code": "000000",
             "new_password": "Br4nd-New!pw", "new_password2": "Br4nd-New!pw"},
            format="json",
        )
        self.assertEqual(bad.status_code, 400)

    def test_weak_new_password_rejected(self):
        resp = self.client.post(reverse("password-reset"), {"email": "reset@x.com"}, format="json")
        code = resp.data["dev_otp"]
        weak = self.client.post(
            reverse("password-reset-confirm"),
            {"email": "reset@x.com", "code": code,
             "new_password": "123456", "new_password2": "123456"},
            format="json",
        )
        self.assertEqual(weak.status_code, 400)
