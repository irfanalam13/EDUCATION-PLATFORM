from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AccountAuthFlowTests(APITestCase):
    def test_register_requires_unique_email_and_returns_student_role(self):
        payload = {
            "username": "sita",
            "email": "sita@example.com",
            "first_name": "Sita",
            "last_name": "Shrestha",
            "password": "Str0ng-Pass!9",
            "password2": "Str0ng-Pass!9",
            "account_type": "STUDENT",
        }
        response = self.client.post(reverse("register"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], User.Role.STUDENT)
        self.assertEqual(User.objects.filter(email="sita@example.com").count(), 1)

        duplicate = self.client.post(
            reverse("register"),
            {**payload, "username": "sita-2"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", duplicate.data)

    def test_login_sets_http_only_token_cookies(self):
        user = User.objects.create_user(
            username="ram",
            email="ram@example.com",
            password="secret123",
        )

        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": user.username, "password": "secret123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
