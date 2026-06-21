from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.academics.models import Chapter, Level, Subject, Topic
from apps.assessment.models import QuizResult, QuizSession
from apps.institutions.models import (
    Assignment,
    Batch,
    BatchStaff,
    Enrollment,
    Grade,
    Institution,
    InstitutionMember,
    Submission,
)
from apps.progress.models import DailyActivity, TopicProgress

from .models import AnalyticsReport

User = get_user_model()


class AnalyticsTestBase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.today = timezone.localdate()

        # Curriculum
        level = Level.objects.create(name="Grade 10", order=1)
        cls.subject = Subject.objects.create(level=level, name="Mathematics", code="MATH10")
        chapter = Chapter.objects.create(subject=cls.subject, title="Algebra", number=1)
        cls.topic = Topic.objects.create(chapter=chapter, title="Linear Equations")
        cls.topic2 = Topic.objects.create(chapter=chapter, title="Quadratics")

        # People
        cls.admin = User.objects.create_user("admin1", password="x")
        cls.teacher = User.objects.create_user("teacher1", password="x")
        cls.student_a = User.objects.create_user("studenta", password="x")
        cls.student_b = User.objects.create_user("studentb", password="x")
        cls.outsider = User.objects.create_user("outsider", password="x")

        # Institution + members
        cls.inst = Institution.objects.create(name="Sunrise College", slug="sunrise")
        InstitutionMember.objects.create(
            institution=cls.inst, user=cls.admin,
            role=InstitutionMember.Role.ADMIN, status=InstitutionMember.Status.ACTIVE,
        )
        InstitutionMember.objects.create(
            institution=cls.inst, user=cls.teacher,
            role=InstitutionMember.Role.TEACHER, status=InstitutionMember.Status.ACTIVE,
        )
        for s in (cls.student_a, cls.student_b):
            InstitutionMember.objects.create(
                institution=cls.inst, user=s,
                role=InstitutionMember.Role.STUDENT, status=InstitutionMember.Status.ACTIVE,
            )

        # Batch taught by teacher, both students approved
        cls.batch = Batch.objects.create(institution=cls.inst, name="Math A")
        BatchStaff.objects.create(batch=cls.batch, user=cls.teacher, role=BatchStaff.Role.TEACHER)
        for s in (cls.student_a, cls.student_b):
            Enrollment.objects.create(batch=cls.batch, user=s, status=Enrollment.Status.APPROVED)

        # Activity + mastery
        DailyActivity.objects.create(user=cls.student_a, date=cls.today, minutes=60)
        DailyActivity.objects.create(user=cls.student_b, date=cls.today, minutes=30)
        TopicProgress.objects.create(user=cls.student_a, topic=cls.topic, mastery=80.0, total_answered=10, correct=8)
        TopicProgress.objects.create(user=cls.student_b, topic=cls.topic, mastery=40.0, total_answered=10, correct=4)
        TopicProgress.objects.create(user=cls.student_a, topic=cls.topic2, mastery=20.0, total_answered=5, correct=1)

        # Quiz performance
        session = QuizSession.objects.create(user=cls.student_a, subject=cls.subject, topic=cls.topic)
        QuizResult.objects.create(session=session, total=10, correct=8, score=8.0, percentage=80.0)

        # One published assignment, one graded submission
        cls.assignment = Assignment.objects.create(
            batch=cls.batch, title="HW1", visibility=Assignment.Visibility.PUBLISHED,
        )
        sub = Submission.objects.create(assignment=cls.assignment, user=cls.student_a, status="GRADED")
        Grade.objects.create(submission=sub, score=90.0)

    def url(self, path, **params):
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"/api/analytics/{path}?{qs}" if qs else f"/api/analytics/{path}"


class InstitutionAnalyticsTests(AnalyticsTestBase):
    def test_requires_authentication(self):
        res = self.client.get(self.url("institution/", institution_id=self.inst.id))
        self.assertIn(res.status_code, (401, 403))

    def test_student_member_forbidden(self):
        self.client.force_authenticate(self.student_a)
        res = self.client.get(self.url("institution/", institution_id=self.inst.id))
        self.assertEqual(res.status_code, 403)

    def test_admin_sees_metrics(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get(self.url("institution/", institution_id=self.inst.id))
        self.assertEqual(res.status_code, 200)
        m = res.data["metrics"]
        self.assertEqual(m["active_students"], 2)
        self.assertEqual(m["daily_active_users"], 2)
        self.assertEqual(m["learning_hours"], 1.5)  # (60+30)/60
        self.assertEqual(m["quiz_performance"], 80.0)
        # avg mastery across the 3 TopicProgress rows = (80+40+20)/3
        self.assertAlmostEqual(m["avg_mastery"], 46.7, places=1)
        # 1 published assignment x 2 approved students = 2 expected; 1 submission
        self.assertEqual(m["assignments"]["expected_submissions"], 2)
        self.assertEqual(m["assignments"]["submissions"], 1)
        self.assertEqual(m["assignments"]["completion_rate"], 50.0)
        self.assertEqual(len(res.data["trend"]), 30)

    def test_admin_of_other_institution_forbidden(self):
        other = Institution.objects.create(name="Other", slug="other")
        InstitutionMember.objects.create(
            institution=other, user=self.outsider,
            role=InstitutionMember.Role.ADMIN, status=InstitutionMember.Status.ACTIVE,
        )
        self.client.force_authenticate(self.outsider)
        res = self.client.get(self.url("institution/", institution_id=self.inst.id))
        self.assertEqual(res.status_code, 403)


class TeacherAnalyticsTests(AnalyticsTestBase):
    def test_teacher_sees_own_metrics(self):
        self.client.force_authenticate(self.teacher)
        res = self.client.get(self.url("teacher/", institution_id=self.inst.id))
        self.assertEqual(res.status_code, 200)
        m = res.data["metrics"]
        self.assertEqual(m["students_taught"], 2)
        self.assertEqual(m["average_student_score"], 90.0)
        self.assertTrue(m["weak_topics"])  # ordered by lowest mastery
        self.assertEqual(m["weak_topics"][0]["topic"], "Quadratics")  # mastery 20

    def test_teacher_cannot_view_other_teacher(self):
        self.client.force_authenticate(self.teacher)
        res = self.client.get(self.url("teacher/", institution_id=self.inst.id, teacher_id=self.admin.id))
        self.assertEqual(res.status_code, 403)

    def test_admin_can_view_any_teacher(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get(self.url("teacher/", institution_id=self.inst.id, teacher_id=self.teacher.id))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["metrics"]["students_taught"], 2)


class StudentAnalyticsTests(AnalyticsTestBase):
    def test_student_sees_self(self):
        self.client.force_authenticate(self.student_a)
        res = self.client.get(self.url("student/", student_id=self.student_a.id))
        self.assertEqual(res.status_code, 200)
        m = res.data["metrics"]
        self.assertEqual(m["quiz_performance"], 80.0)
        self.assertEqual(m["assignments_graded"], 1)

    def test_student_cannot_view_peer(self):
        self.client.force_authenticate(self.student_a)
        res = self.client.get(
            self.url("student/", student_id=self.student_b.id, institution_id=self.inst.id)
        )
        self.assertEqual(res.status_code, 403)

    def test_teacher_can_view_their_student(self):
        self.client.force_authenticate(self.teacher)
        res = self.client.get(
            self.url("student/", student_id=self.student_a.id, institution_id=self.inst.id)
        )
        self.assertEqual(res.status_code, 200)


class SubjectAnalyticsTests(AnalyticsTestBase):
    def test_subject_distribution(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get(
            self.url("subject/", institution_id=self.inst.id, subject_id=self.subject.id)
        )
        self.assertEqual(res.status_code, 200)
        dist = res.data["topic_mastery_distribution"]
        # masteries: 80, 40, 20 -> bands 75-100:1, 25-50:1, 0-25:1
        self.assertEqual(dist["75-100"], 1)
        self.assertEqual(dist["25-50"], 1)
        self.assertEqual(dist["0-25"], 1)
        self.assertTrue(res.data["most_difficult_topics"])

    def test_subject_overview_lists_subjects(self):
        self.client.force_authenticate(self.admin)
        res = self.client.get(self.url("subject/", institution_id=self.inst.id))
        self.assertEqual(res.status_code, 200)
        names = [s["subject"] for s in res.data["subjects"]]
        self.assertIn("Mathematics", names)


class ReportTests(AnalyticsTestBase):
    def test_generate_pdf_and_list(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            "/api/analytics/report/generate/",
            {"institution_id": self.inst.id, "period": "MONTHLY", "file_format": "PDF"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["status"], "READY")
        self.assertTrue(res.data["download_url"])
        self.assertEqual(AnalyticsReport.objects.count(), 1)

        listed = self.client.get(self.url("reports/", institution_id=self.inst.id))
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data), 1)

    def test_generate_excel(self):
        self.client.force_authenticate(self.admin)
        res = self.client.post(
            "/api/analytics/report/generate/",
            {"institution_id": self.inst.id, "period": "SEMESTER", "file_format": "XLSX"},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertTrue(res.data["download_url"].endswith(".xlsx"))

    def test_non_admin_cannot_generate(self):
        self.client.force_authenticate(self.student_a)
        res = self.client.post(
            "/api/analytics/report/generate/",
            {"institution_id": self.inst.id},
            format="json",
        )
        self.assertEqual(res.status_code, 403)
