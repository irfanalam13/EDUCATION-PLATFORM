"""Phase 7: the consolidated MCQ practice endpoint preserves the client contract.

Web QuizPlayer + mobile QuizScreen now call /api/assessment/mcq/questions/.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.academics.models import Level, Subject, Chapter, Topic
from apps.assessment.models import MCQQuestion, MCQOption, MCQAttempt
from apps.gamification.models import XpTransaction

User = get_user_model()


class MCQPracticeEndpointTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="quiz", email="q@x.com", password="pw-1234aa")
        level = Level.objects.create(name="Grade 10")
        subject = Subject.objects.create(level=level, name="Math")
        chapter = Chapter.objects.create(subject=subject, title="Algebra", number=1)
        cls.topic = Topic.objects.create(chapter=chapter, title="Linear Equations")
        cls.q = MCQQuestion.objects.create(question_text="2+2=?", topic=cls.topic)
        cls.correct = MCQOption.objects.create(question=cls.q, text="4", is_correct=True)
        cls.wrong = MCQOption.objects.create(question=cls.q, text="5", is_correct=False)

    def setUp(self):
        self.client.force_authenticate(self.user)

    def test_list_returns_client_contract(self):
        resp = self.client.get(f"/api/assessment/mcq/questions/?topic={self.topic.id}")
        self.assertEqual(resp.status_code, 200)
        results = resp.data["results"] if isinstance(resp.data, dict) else resp.data
        self.assertEqual(len(results), 1)
        q = results[0]
        # Contract the web/mobile quiz expects: choices[].choice_text, no answer key.
        self.assertIn("choices", q)
        self.assertIn("choice_text", q["choices"][0])
        self.assertNotIn("is_correct", q["choices"][0])
        self.assertNotIn("explanation", q)

    def test_answer_correct_awards_xp(self):
        resp = self.client.post(
            f"/api/assessment/mcq/questions/{self.q.id}/answer/",
            {"choice_id": self.correct.id}, format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["is_correct"])
        self.assertTrue(MCQAttempt.objects.filter(user=self.user, question=self.q, is_correct=True).exists())
        self.assertTrue(
            XpTransaction.objects.filter(user=self.user, source="practice_correct").exists()
        )

    def test_answer_wrong_no_xp(self):
        resp = self.client.post(
            f"/api/assessment/mcq/questions/{self.q.id}/answer/",
            {"choice_id": self.wrong.id}, format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data["is_correct"])
        self.assertFalse(
            XpTransaction.objects.filter(user=self.user, source="practice_correct").exists()
        )
