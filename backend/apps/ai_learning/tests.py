from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.academics.models import Level, Subject, Chapter, Topic
from apps.assessment.models import MCQQuestion, MCQOption
from apps.progress.models import TopicProgress
from apps.ai_learning.models import WeakTopic, StudyRecommendation, StudyPlan, MasteryBand
from apps.ai_learning.services.mastery_calculator import mastery_band
from apps.ai_learning.services import forgetting_curve

User = get_user_model()


class ServiceUnitTests(TestCase):
    def test_mastery_band_thresholds(self):
        self.assertEqual(mastery_band(95), MasteryBand.MASTERED)
        self.assertEqual(mastery_band(65), MasteryBand.PROFICIENT)
        self.assertEqual(mastery_band(40), MasteryBand.DEVELOPING)
        self.assertEqual(mastery_band(5), MasteryBand.BEGINNER)

    def test_forgetting_curve(self):
        now = timezone.now()
        tp = TopicProgress(
            mastery=50, correct=5, total_answered=10, interval_days=2, ease=2.0,
            last_practiced_at=now - timedelta(days=1),
            next_review_at=now - timedelta(hours=1),
        )
        r = forgetting_curve.retention(tp, now=now)
        self.assertTrue(0.0 <= r <= 1.0)
        self.assertTrue(forgetting_curve.is_due(tp, now=now))  # next_review passed
        self.assertGreater(forgetting_curve.days_to_target(tp, target=80), 0)


class AIEngineAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="learner", email="l@x.com", password="pw-1234aa")
        level = Level.objects.create(name="Grade 10")
        subject = Subject.objects.create(level=level, name="Math")
        chapter = Chapter.objects.create(subject=subject, title="Algebra", number=1)
        cls.weak = Topic.objects.create(chapter=chapter, title="Quadratics", order=1)
        cls.strong = Topic.objects.create(chapter=chapter, title="Linear", order=2)

        now = timezone.now()
        # Weak: low mastery + low accuracy + stale, review overdue.
        TopicProgress.objects.create(
            user=cls.user, topic=cls.weak, mastery=20.0, correct=2, total_answered=10,
            attempts=3, last_practiced_at=now - timedelta(days=10),
            interval_days=1, ease=2.3, next_review_at=now - timedelta(days=1),
        )
        # Strong: high mastery, recently practiced, not due.
        TopicProgress.objects.create(
            user=cls.user, topic=cls.strong, mastery=90.0, correct=9, total_answered=10,
            attempts=5, last_practiced_at=now, interval_days=10, ease=2.6,
            next_review_at=now + timedelta(days=10),
        )
        # Questions exist for the weak topic (enables a practice recommendation).
        q = MCQQuestion.objects.create(question_text="x^2=4?", topic=cls.weak)
        MCQOption.objects.create(question=q, text="2", is_correct=True)
        MCQOption.objects.create(question=q, text="3", is_correct=False)

    def setUp(self):
        self.client.force_authenticate(self.user)

    def test_generate_plan_populates_everything(self):
        resp = self.client.post("/api/ai/generate-plan/")
        self.assertEqual(resp.status_code, 201, resp.content)
        self.assertEqual(resp.data["weak_topics"], 1)
        self.assertGreaterEqual(resp.data["recommendations"], 1)
        self.assertIsNotNone(resp.data["plan"])
        self.assertGreaterEqual(len(resp.data["plan"]["sessions"]), 1)

        # Persisted
        self.assertTrue(WeakTopic.objects.filter(user=self.user, topic=self.weak).exists())
        self.assertFalse(WeakTopic.objects.filter(user=self.user, topic=self.strong).exists())
        self.assertTrue(StudyRecommendation.objects.filter(user=self.user).exists())
        self.assertTrue(StudyPlan.objects.filter(user=self.user).exists())

    def test_get_endpoints(self):
        self.client.post("/api/ai/generate-plan/")

        wt = self.client.get("/api/ai/weak-topics/")
        self.assertEqual(wt.status_code, 200)
        self.assertEqual(len(wt.data), 1)
        self.assertEqual(wt.data[0]["topic"], self.weak.id)

        recs = self.client.get("/api/ai/recommendations/")
        self.assertEqual(recs.status_code, 200)
        self.assertGreaterEqual(len(recs.data), 1)

        mastery = self.client.get("/api/ai/mastery/")
        self.assertEqual(mastery.status_code, 200)
        self.assertEqual(len(mastery.data["topics"]), 2)
        self.assertIn("band_distribution", mastery.data)
        self.assertGreater(mastery.data["overall_mastery"], 0)

        plan = self.client.get("/api/ai/study-plan/")
        self.assertEqual(plan.status_code, 200)
        self.assertGreaterEqual(len(plan.data["sessions"]), 1)

    def test_requires_auth(self):
        self.client.force_authenticate(None)
        self.assertIn(self.client.get("/api/ai/mastery/").status_code, (401, 403))
