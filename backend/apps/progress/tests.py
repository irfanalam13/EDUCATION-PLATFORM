from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.academics.models import Chapter, Level, Subject, Topic

from .models import DailyActivity, TopicProgress, UserGoal


class ProgressEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="hari",
            email="hari@example.com",
            password="secret123",
        )
        self.client.force_authenticate(self.user)

        level = Level.objects.create(name="Grade 10", order=1)
        subject = Subject.objects.create(level=level, name="Mathematics", order=1)
        chapter = Chapter.objects.create(subject=subject, title="Algebra", number=1, order=1)
        self.topic = Topic.objects.create(chapter=chapter, title="Linear Equations", order=1)

    def test_dashboard_endpoint_returns_expected_payload(self):
        TopicProgress.objects.create(
            user=self.user,
            topic=self.topic,
            total_answered=10,
            correct=7,
            mastery=70,
        )
        DailyActivity.objects.create(user=self.user, minutes=35, attempted=10, correct=7, xp_earned=20)
        UserGoal.objects.create(user=self.user, daily_minutes_goal=30)

        response = self.client.get(reverse("progress-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("totals", response.data)
        self.assertEqual(response.data["totals"]["topics"], 1)
        self.assertIn("weak_topics", response.data)
        self.assertIn("activity_7d", response.data)

    def test_recommendations_route_is_wired(self):
        response = self.client.get(reverse("progress-recommendations"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
