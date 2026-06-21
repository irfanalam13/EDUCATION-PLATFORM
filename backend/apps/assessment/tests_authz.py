"""Phase 2b regression tests: answer-key exposure in the assessment app."""
from __future__ import annotations

from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.assessment.models import PracticeQuestion
from apps.assessment.serializers.bank import PracticeQuestionSerializer

User = get_user_model()


class PracticeAnswerLeakTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.q = PracticeQuestion.objects.create(
            prompt="Solve x+1=2", answer_text="x=1", explanation="trivial",
        )
        cls.student = User.objects.create_user(username="stu", email="s@x.com", password="pw-1234aa")
        cls.staff = User.objects.create_user(
            username="staff", email="t@x.com", password="pw-1234aa", is_staff=True
        )

    def _rep(self, user):
        request = SimpleNamespace(user=user)
        return PracticeQuestionSerializer(self.q, context={"request": request}).data

    def test_student_does_not_see_answer_text(self):
        data = self._rep(self.student)
        self.assertNotIn("answer_text", data)

    def test_staff_sees_answer_text(self):
        data = self._rep(self.staff)
        self.assertEqual(data.get("answer_text"), "x=1")
