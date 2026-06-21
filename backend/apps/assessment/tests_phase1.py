"""Phase-1 integration tests: the full learning loop fires end-to-end.

Quiz finish -> XP awarded (no rollback) -> progress updated -> daily activity
-> streak -> leaderboard recompute -> notification.

These run with CELERY_TASK_ALWAYS_EAGER (set in dev/test settings) and use
captureOnCommitCallbacks so transaction.on_commit hooks actually execute.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.academics.models import Level, Subject, Chapter, Topic
from apps.assessment.models import (
    QuizSession,
    QuizSessionQuestion,
    QuizResult,
)
from apps.assessment.models.bank import MCQQuestion, MCQOption
from apps.assessment.models.quiz import QuizMode, SessionState
from apps.assessment.services import (
    apply_answer_to_session_question,
    finish_session_and_compute_result,
)
from apps.gamification.models import UserGamificationProfile, XpTransaction
from apps.gamification.services.xp import award_xp
from apps.notifications.models import Notification
from apps.progress.models import TopicProgress, DailyActivity, StudyStreak

User = get_user_model()


class XpRollbackRegressionTest(TestCase):
    """The original bug: award_xp fired .delay() inside its atomic block, so a
    broker error rolled the XP back. With on_commit + eager mode it must persist."""

    def test_award_xp_persists_and_followups_run(self):
        user = User.objects.create_user(username="lia", email="lia@x.com", password="pw")
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            tx = award_xp(user=user, source="quiz_finish", points=30,
                          idempotency_key="t1")
        self.assertEqual(tx.status, XpTransaction.STATUS_AWARDED)
        self.assertGreater(tx.points_awarded, 0)

        profile = UserGamificationProfile.objects.get(user=user)
        self.assertEqual(profile.total_xp, tx.points_awarded)  # not rolled back
        self.assertGreaterEqual(len(callbacks), 1)             # follow-ups scheduled

    def test_award_xp_is_idempotent(self):
        user = User.objects.create_user(username="ido", email="ido@x.com", password="pw")
        with self.captureOnCommitCallbacks(execute=True):
            tx1 = award_xp(user=user, source="quiz_finish", points=30, idempotency_key="dup")
        with self.captureOnCommitCallbacks(execute=True):
            tx2 = award_xp(user=user, source="quiz_finish", points=30, idempotency_key="dup")
        self.assertEqual(tx1.id, tx2.id)
        self.assertEqual(XpTransaction.objects.filter(user=user).count(), 1)


class PermissionDefaultTest(TestCase):
    """Secure-by-default: public catalogue stays open, everything else 401s."""

    def setUp(self):
        from rest_framework.test import APIClient
        self.client = APIClient()

    def test_academics_catalogue_is_public(self):
        for path in ("/api/academics/levels/", "/api/academics/subjects/",
                     "/api/academics/topics/"):
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, f"{path} should be public")

    def test_protected_endpoint_requires_auth(self):
        # progress dashboard must reject anonymous access now.
        resp = self.client.get("/api/progress/dashboard/")
        self.assertIn(resp.status_code, (401, 403),
                      "protected endpoint must require authentication")


class QuizFinishChainTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.level = Level.objects.create(name="Grade 10")
        cls.subject = Subject.objects.create(level=cls.level, name="Mathematics")
        cls.chapter = Chapter.objects.create(subject=cls.subject, title="Algebra", number=1)
        cls.topic = Topic.objects.create(chapter=cls.chapter, title="Linear Equations")

    def _build_session(self, user, n_questions=2):
        session = QuizSession.objects.create(
            user=user, mode=QuizMode.PRACTICE, topic=self.topic,
            requested_count=n_questions,
        )
        session.mark_started()
        session.save(update_fields=["state", "started_at"])
        questions = []
        for i in range(n_questions):
            q = MCQQuestion.objects.create(question_text=f"Q{i}", topic=self.topic)
            correct = MCQOption.objects.create(question=q, text="right", is_correct=True)
            MCQOption.objects.create(question=q, text="wrong", is_correct=False)
            QuizSessionQuestion.objects.create(session=session, question=q, order=i)
            questions.append((q, correct))
        return session, questions

    def test_full_chain(self):
        user = User.objects.create_user(username="amrit", email="amrit@x.com", password="pw")
        session, questions = self._build_session(user, n_questions=2)

        for q, correct in questions:
            apply_answer_to_session_question(
                session, {"question_id": q.id, "answer": correct.id, "time_spent_seconds": 5}
            )

        with self.captureOnCommitCallbacks(execute=True):
            result = finish_session_and_compute_result(session)

        # Quiz scored
        self.assertEqual(result.correct, 2)
        self.assertEqual(result.total, 2)
        self.assertGreater(result.xp_awarded, 0)
        session.refresh_from_db()
        self.assertEqual(session.state, SessionState.FINISHED)

        # XP awarded (real engine, persisted)
        self.assertTrue(
            XpTransaction.objects.filter(user=user, source="quiz_finish",
                                         idempotency_key=f"quiz:{session.id}").exists()
        )
        self.assertEqual(UserGamificationProfile.objects.get(user=user).total_xp,
                         result.xp_awarded)

        # Progress updated (topic resolved by title)
        tp = TopicProgress.objects.get(user=user, topic=self.topic)
        self.assertEqual(tp.correct, 2)
        self.assertEqual(tp.total_answered, 2)
        self.assertGreater(tp.mastery, 0)

        # Daily activity + streak
        da = DailyActivity.objects.get(user=user)
        self.assertEqual(da.attempted, 2)
        self.assertEqual(da.correct, 2)
        self.assertEqual(da.xp_earned, result.xp_awarded)
        self.assertEqual(StudyStreak.objects.get(user=user).current_streak, 1)

        # Notification fired
        self.assertTrue(
            Notification.objects.filter(user=user, type="QUIZ").exists()
        )

    def test_finish_is_idempotent_on_xp(self):
        """Finishing twice must not double-award XP (guarded by state + idem key)."""
        user = User.objects.create_user(username="dup2", email="dup2@x.com", password="pw")
        session, questions = self._build_session(user, n_questions=1)
        q, correct = questions[0]
        apply_answer_to_session_question(
            session, {"question_id": q.id, "answer": correct.id}
        )
        with self.captureOnCommitCallbacks(execute=True):
            finish_session_and_compute_result(session)
        first_xp = UserGamificationProfile.objects.get(user=user).total_xp
        # Second finish raises (state no longer IN_PROGRESS) — XP unchanged.
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            finish_session_and_compute_result(session)
        self.assertEqual(UserGamificationProfile.objects.get(user=user).total_xp, first_xp)
