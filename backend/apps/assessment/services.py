import logging
from typing import Dict, Any

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.assessment.models import (
    QuizSession,
    QuizSessionQuestion,
    QuizResult,
    MCQOption,
)
from apps.assessment.models.quiz import SessionState

logger = logging.getLogger(__name__)


def award_xp_for_quiz(user, *, correct: int, total: int, mode: str, session_id: int) -> int:
    """Award real XP for a finished quiz via the gamification engine.

    Idempotent per session (``idempotency_key="quiz:<id>"``) so a retried finish
    never double-awards. Returns the points actually credited (after caps/
    multipliers), which we persist on ``QuizResult.xp_awarded``.
    """
    if total <= 0:
        return 0

    base = 5 if mode == QuizMode_PRACTICE else 10
    points = int(base * correct)
    if points <= 0:
        return 0

    from apps.gamification.services.xp import award_xp

    tx = award_xp(
        user=user,
        source="quiz_finish",
        points=points,
        idempotency_key=f"quiz:{session_id}",
        object_type="quiz_session",
        object_id=str(session_id),
        metadata={"correct": correct, "total": total, "mode": mode},
    )
    return int(getattr(tx, "points_awarded", 0) or 0)


# Local constant to avoid importing the enum at module top (keeps imports light).
QuizMode_PRACTICE = "PRACTICE"


def _resolve_topic(session: QuizSession):
    """Return the session's academics.Topic (now a real FK), or None."""
    return session.topic


def _difficulty_mix_for_session(session: QuizSession) -> dict:
    """Count answered questions by difficulty for mastery weighting."""
    mix = {"easy": 0, "medium": 0, "hard": 0}
    rows = (
        QuizSessionQuestion.objects.filter(session=session)
        .values_list("question__difficulty", flat=True)
    )
    for d in rows:
        if d == "EASY":
            mix["easy"] += 1
        elif d == "HARD":
            mix["hard"] += 1
        else:
            mix["medium"] += 1
    return mix


@transaction.atomic
def apply_answer_to_session_question(session: QuizSession, payload: Dict[str, Any]) -> QuizSessionQuestion:
    if session.state != SessionState.IN_PROGRESS:
        raise ValidationError("You can only answer when session is IN_PROGRESS.")

    question_id = payload["question_id"]
    option_id = payload["answer"]
    time_spent = payload.get("time_spent_seconds", 0)

    try:
        sq = QuizSessionQuestion.objects.select_for_update().get(session=session, question_id=question_id)
    except QuizSessionQuestion.DoesNotExist:
        raise ValidationError("This question is not part of the session.")

    # validate option belongs to that question
    try:
        opt = MCQOption.objects.get(id=option_id, question_id=question_id)
    except MCQOption.DoesNotExist:
        raise ValidationError("Invalid option for this question.")

    sq.selected_option_id = opt.id
    sq.is_correct = bool(opt.is_correct)
    sq.time_spent_seconds = int(time_spent)
    sq.save(update_fields=["selected_option_id", "is_correct", "time_spent_seconds"])
    return sq


@transaction.atomic
def finish_session_and_compute_result(session: QuizSession) -> QuizResult:
    if session.state != SessionState.IN_PROGRESS:
        raise ValidationError("You can only finish when session is IN_PROGRESS.")

    # Lock session questions for safe scoring
    sqs = list(
        QuizSessionQuestion.objects.select_for_update()
        .filter(session=session)
        .only("id", "is_correct")
    )

    total = len(sqs)
    correct = sum(1 for x in sqs if x.is_correct is True)
    percentage = (correct / total) * 100.0 if total else 0.0
    score = correct  # simple score = correct count

    # 1) XP via gamification engine (also triggers badges/leaderboards/quests
    #    and level-up notification on commit).
    xp = award_xp_for_quiz(
        session.user, correct=correct, total=total, mode=session.mode, session_id=session.id
    )

    session.mark_finished()
    session.save(update_fields=["state", "finished_at"])

    result, _created = QuizResult.objects.update_or_create(
        session=session,
        defaults={
            "total": total,
            "correct": correct,
            "percentage": percentage,
            "score": score,
            "xp_awarded": xp,
        },
    )

    # 2) Progress, daily activity and streak. Best-effort: a failure here must
    #    not roll back the result/XP the student already earned.
    try:
        from apps.progress.services import (
            update_topic_progress,
            update_daily_activity,
            update_streak,
        )

        topic = _resolve_topic(session)
        if topic is not None:
            update_topic_progress(
                session.user, topic, score=correct, total=total,
                difficulty_mix=_difficulty_mix_for_session(session),
            )
        update_daily_activity(session.user, attempted=total, correct=correct, xp=xp)
        update_streak(session.user)
    except Exception:  # pragma: no cover - defensive
        logger.exception("Progress update failed for quiz session %s", session.id)

    # 3) Quiz-completed notification (after commit).
    def _notify_quiz_done():
        try:
            from apps.notifications.services import create_notification
            create_notification(
                user=session.user,
                title="Quiz completed ✅",
                body=f"You scored {correct}/{total} ({percentage:.0f}%) and earned {xp} XP.",
                type="QUIZ",
                data={
                    "event": "quiz_completed",
                    "session_id": session.id,
                    "score": correct,
                    "total": total,
                    "xp": xp,
                },
            )
        except Exception:  # pragma: no cover - defensive
            logger.exception("Quiz notification failed for session %s", session.id)

    transaction.on_commit(_notify_quiz_done)

    return result
