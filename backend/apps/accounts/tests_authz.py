"""Phase 2b regression tests: accounts PII/verification and password policy."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.serializers import MeSerializer, RegisterSerializer

User = get_user_model()


class MeSerializerTest(TestCase):
    def test_cannot_self_set_email_verified(self):
        user = User.objects.create_user(username="u1", email="u1@x.com", password="pw-1234aa")
        self.assertFalse(user.email_verified)
        ser = MeSerializer(
            instance=user,
            data={"email_verified": True, "email": "evil@x.com", "first_name": "Z"},
            partial=True,
        )
        self.assertTrue(ser.is_valid(), ser.errors)
        ser.save()
        user.refresh_from_db()
        # email/email_verified are read-only; first_name still updates.
        self.assertFalse(user.email_verified)
        self.assertEqual(user.email, "u1@x.com")
        self.assertEqual(user.first_name, "Z")


class RegisterPasswordPolicyTest(TestCase):
    def _payload(self, pw):
        return {
            "username": "newbie", "email": "new@x.com",
            "first_name": "N", "last_name": "B",
            "password": pw, "password2": pw,
        }

    def test_weak_password_rejected(self):
        ser = RegisterSerializer(data=self._payload("123456"))
        self.assertFalse(ser.is_valid())
        self.assertIn("password", ser.errors)

    def test_strong_password_accepted(self):
        ser = RegisterSerializer(data=self._payload("Str0ng-Pass!9"))
        self.assertTrue(ser.is_valid(), ser.errors)
