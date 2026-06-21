"""Compute-on-read analytics aggregations.

Every metric is derived live from the canonical models (no duplicated state):
  - membership/roles ...... apps.institutions (InstitutionMember, Batch, BatchStaff, Enrollment)
  - coursework ............ apps.institutions (Assignment, Submission, Grade)
  - activity/time ......... apps.progress.DailyActivity, StudyStreak
  - mastery/topics ........ apps.progress.TopicProgress
  - quiz performance ...... apps.assessment.QuizResult / QuizSession / QuizSessionQuestion
  - gamification .......... apps.gamification.UserGamificationProfile

The InstitutionDailySnapshot table only persists a daily time-series for history;
the dashboards call these functions directly.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from apps.assessment.models import QuizResult, QuizSessionQuestion
from apps.gamification.models import UserGamificationProfile
from apps.institutions.models import (
    Assignment,
    Batch,
    BatchStaff,
    Enrollment,
    InstitutionMember,
    Submission,
)
from apps.progress.models import DailyActivity, StudyStreak, TopicProgress

ACTIVE = InstitutionMember.Status.ACTIVE
ROLE_STUDENT = InstitutionMember.Role.STUDENT
ENROLL_APPROVED = Enrollment.Status.APPROVED
PUBLISHED = Assignment.Visibility.PUBLISHED
TEACHING_ROLES = [BatchStaff.Role.OWNER, BatchStaff.Role.TEACHER, BatchStaff.Role.TA]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _pct(part: float, whole: float) -> float:
    return round(100.0 * part / whole, 1) if whole else 0.0


def _round(value, ndigits: int = 1) -> float:
    return round(float(value), ndigits) if value is not None else 0.0


def institution_student_ids(institution_id: int) -> list[int]:
    """User ids of ACTIVE student members of the institution."""
    return list(
        InstitutionMember.objects.filter(
            institution_id=institution_id, role=ROLE_STUDENT, status=ACTIVE
        ).values_list("user_id", flat=True)
    )


def _assignment_completion(batch_ids: list[int] | None = None, institution_id: int | None = None) -> dict:
    """Completion = submissions / (published assignments x approved students), per batch."""
    batches = Batch.objects.all()
    if institution_id is not None:
        batches = batches.filter(institution_id=institution_id)
    if batch_ids is not None:
        batches = batches.filter(id__in=batch_ids)

    expected = 0
    published_total = 0
    for b in batches.values_list("id", flat=True):
        pub = Assignment.objects.filter(batch_id=b, visibility=PUBLISHED).count()
        enrolled = Enrollment.objects.filter(batch_id=b, status=ENROLL_APPROVED).count()
        expected += pub * enrolled
        published_total += pub

    sub_q = Submission.objects.filter(assignment__visibility=PUBLISHED)
    if institution_id is not None:
        sub_q = sub_q.filter(assignment__batch__institution_id=institution_id)
    if batch_ids is not None:
        sub_q = sub_q.filter(assignment__batch_id__in=batch_ids)
    submitted = sub_q.count()
    graded = sub_q.filter(status="GRADED").count()

    return {
        "published_assignments": published_total,
        "expected_submissions": expected,
        "submissions": submitted,
        "graded": graded,
        "completion_rate": _pct(submitted, expected),
    }


def _daily_trend(user_ids: list[int], days: int) -> list[dict]:
    """Per-day active users / learning minutes / avg quiz score for a window."""
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)

    activity = {
        row["date"]: row
        for row in DailyActivity.objects.filter(user_id__in=user_ids, date__gte=start)
        .values("date")
        .annotate(active_users=Count("user_id", distinct=True), minutes=Sum("minutes"))
    }
    quiz = {
        row["computed_at__date"]: row["avg"]
        for row in QuizResult.objects.filter(
            session__user_id__in=user_ids, computed_at__date__gte=start
        )
        .values("computed_at__date")
        .annotate(avg=Avg("percentage"))
    }

    out = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        a = activity.get(day, {})
        out.append(
            {
                "date": day.isoformat(),
                "active_users": a.get("active_users", 0),
                "learning_minutes": a.get("minutes", 0) or 0,
                "avg_quiz_score": _round(quiz.get(day, 0.0)),
            }
        )
    return out


# --------------------------------------------------------------------------- #
# institution
# --------------------------------------------------------------------------- #
def institution_overview(institution_id: int, days: int = 30) -> dict:
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    sids = institution_student_ids(institution_id)
    n = len(sids)

    da = DailyActivity.objects.filter(user_id__in=sids)
    dau = da.filter(date=today).values("user_id").distinct().count()
    mau = da.filter(date__gte=today - timedelta(days=29)).values("user_id").distinct().count()
    active_7d = da.filter(date__gte=today - timedelta(days=6)).values("user_id").distinct().count()
    learning_minutes = da.filter(date__gte=start).aggregate(s=Sum("minutes"))["s"] or 0

    avg_quiz = QuizResult.objects.filter(
        session__user_id__in=sids, computed_at__date__gte=start
    ).aggregate(a=Avg("percentage"))["a"]
    avg_mastery = TopicProgress.objects.filter(user_id__in=sids).aggregate(a=Avg("mastery"))["a"]

    return {
        "institution_id": institution_id,
        "window_days": days,
        "metrics": {
            "active_students": n,
            "daily_active_users": dau,
            "monthly_active_users": mau,
            "learning_hours": _round(learning_minutes / 60.0),
            "quiz_performance": _round(avg_quiz),
            "avg_mastery": _round(avg_mastery),
            "attendance_rate": _pct(active_7d, n),  # % of students active in last 7 days
            "assignments": _assignment_completion(institution_id=institution_id),
        },
        "trend": _daily_trend(sids, days),
    }


def institution_trend(institution_id: int, days: int = 30) -> list[dict]:
    return _daily_trend(institution_student_ids(institution_id), days)


# --------------------------------------------------------------------------- #
# teacher
# --------------------------------------------------------------------------- #
def teacher_batch_ids(institution_id: int, teacher_user_id: int) -> list[int]:
    return list(
        BatchStaff.objects.filter(
            user_id=teacher_user_id, role__in=TEACHING_ROLES, batch__institution_id=institution_id
        ).values_list("batch_id", flat=True)
    )


def teacher_overview(institution_id: int, teacher_user_id: int, days: int = 30) -> dict:
    today = timezone.localdate()
    batch_ids = teacher_batch_ids(institution_id, teacher_user_id)
    taught_ids = list(
        Enrollment.objects.filter(batch_id__in=batch_ids, status=ENROLL_APPROVED)
        .values_list("user_id", flat=True)
        .distinct()
    )
    n = len(taught_ids)

    avg_grade = (
        Submission.objects.filter(assignment__batch_id__in=batch_ids, grade__isnull=False)
        .aggregate(a=Avg("grade__score"))["a"]
    )
    avg_quiz = QuizResult.objects.filter(session__user_id__in=taught_ids).aggregate(
        a=Avg("percentage")
    )["a"]
    active_7d = (
        DailyActivity.objects.filter(user_id__in=taught_ids, date__gte=today - timedelta(days=6))
        .values("user_id")
        .distinct()
        .count()
    )

    weak = list(
        TopicProgress.objects.filter(user_id__in=taught_ids)
        .values("topic_id", "topic__title")
        .annotate(avg_mastery=Avg("mastery"), learners=Count("user_id", distinct=True))
        .order_by("avg_mastery")[:5]
    )
    weak_topics = [
        {
            "topic_id": w["topic_id"],
            "topic": w["topic__title"],
            "avg_mastery": _round(w["avg_mastery"]),
            "learners": w["learners"],
        }
        for w in weak
    ]

    return {
        "institution_id": institution_id,
        "teacher_id": teacher_user_id,
        "window_days": days,
        "batches": len(batch_ids),
        "metrics": {
            "students_taught": n,
            "average_student_score": _round(avg_grade),
            "quiz_performance": _round(avg_quiz),
            "engagement_rate": _pct(active_7d, n),
            "assignment_completion": _assignment_completion(batch_ids=batch_ids),
            "weak_topics": weak_topics,
        },
    }


# --------------------------------------------------------------------------- #
# student
# --------------------------------------------------------------------------- #
def student_overview(student_id: int, days: int = 30) -> dict:
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)

    tp = TopicProgress.objects.filter(user_id=student_id)
    totals = tp.aggregate(c=Sum("correct"), t=Sum("total_answered"), m=Avg("mastery"))
    minutes = (
        DailyActivity.objects.filter(user_id=student_id, date__gte=start).aggregate(s=Sum("minutes"))["s"]
        or 0
    )
    streak = StudyStreak.objects.filter(user_id=student_id).first()
    gp = UserGamificationProfile.objects.filter(user_id=student_id).first()
    avg_quiz = QuizResult.objects.filter(session__user_id=student_id).aggregate(a=Avg("percentage"))["a"]

    weak = list(
        tp.order_by("mastery").values("topic_id", "topic__title", "mastery")[:5]
    )
    subs = Submission.objects.filter(user_id=student_id)

    return {
        "student_id": student_id,
        "window_days": days,
        "metrics": {
            "avg_mastery": _round(totals["m"]),
            "accuracy": _pct(totals["c"] or 0, totals["t"] or 0),
            "learning_hours": _round(minutes / 60.0),
            "current_streak": getattr(streak, "current_streak", 0),
            "best_streak": getattr(streak, "best_streak", 0),
            "total_xp": getattr(gp, "total_xp", 0),
            "level": getattr(gp, "level", 1),
            "quiz_performance": _round(avg_quiz),
            "assignments_submitted": subs.count(),
            "assignments_graded": subs.filter(status="GRADED").count(),
            "weak_topics": [
                {"topic_id": w["topic_id"], "topic": w["topic__title"], "mastery": _round(w["mastery"])}
                for w in weak
            ],
        },
        "trend": _daily_trend([student_id], days),
    }


# --------------------------------------------------------------------------- #
# subject
# --------------------------------------------------------------------------- #
def _mastery_distribution(qs) -> dict:
    """Counts of TopicProgress rows by mastery band (0-25/25-50/50-75/75-100)."""
    bands = qs.aggregate(
        band_0_25=Count("id", filter=Q(mastery__lt=25)),
        band_25_50=Count("id", filter=Q(mastery__gte=25, mastery__lt=50)),
        band_50_75=Count("id", filter=Q(mastery__gte=50, mastery__lt=75)),
        band_75_100=Count("id", filter=Q(mastery__gte=75)),
    )
    return {
        "0-25": bands["band_0_25"],
        "25-50": bands["band_25_50"],
        "50-75": bands["band_50_75"],
        "75-100": bands["band_75_100"],
    }


def subject_analytics(institution_id: int, subject_id: int | None = None, days: int = 90) -> dict:
    sids = institution_student_ids(institution_id)

    if subject_id is None:
        # Per-subject overview across everything the institution's students touched.
        rows = (
            TopicProgress.objects.filter(user_id__in=sids)
            .values("topic__chapter__subject_id", "topic__chapter__subject__name")
            .annotate(avg_mastery=Avg("mastery"), topics=Count("topic_id", distinct=True))
            .order_by("topic__chapter__subject__name")
        )
        subjects = [
            {
                "subject_id": r["topic__chapter__subject_id"],
                "subject": r["topic__chapter__subject__name"],
                "avg_mastery": _round(r["avg_mastery"]),
                "topics": r["topics"],
            }
            for r in rows
            if r["topic__chapter__subject_id"] is not None
        ]
        return {"institution_id": institution_id, "subjects": subjects}

    tp = TopicProgress.objects.filter(user_id__in=sids, topic__chapter__subject_id=subject_id)
    avg_score = tp.aggregate(a=Avg("mastery"))["a"]

    # Hardest topics by lowest avg mastery.
    hardest = [
        {"topic_id": r["topic_id"], "topic": r["topic__title"], "avg_mastery": _round(r["avg_mastery"])}
        for r in tp.values("topic_id", "topic__title")
        .annotate(avg_mastery=Avg("mastery"))
        .order_by("avg_mastery")[:10]
    ]

    # Highest failure topics from answered quiz questions.
    answered = QuizSessionQuestion.objects.filter(
        session__user_id__in=sids,
        question__topic__chapter__subject_id=subject_id,
        is_correct__isnull=False,
    )
    failure_rows = (
        answered.values("question__topic_id", "question__topic__title")
        .annotate(answered=Count("id"), wrong=Count("id", filter=Q(is_correct=False)))
        .filter(answered__gt=0)
    )
    highest_failure = sorted(
        (
            {
                "topic_id": r["question__topic_id"],
                "topic": r["question__topic__title"],
                "failure_rate": _pct(r["wrong"], r["answered"]),
                "answered": r["answered"],
            }
            for r in failure_rows
        ),
        key=lambda x: x["failure_rate"],
        reverse=True,
    )[:10]

    return {
        "institution_id": institution_id,
        "subject_id": subject_id,
        "average_score": _round(avg_score),
        "most_difficult_topics": hardest,
        "highest_failure_topics": highest_failure,
        "topic_mastery_distribution": _mastery_distribution(tp),
    }
