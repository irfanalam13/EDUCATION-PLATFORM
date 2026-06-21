from django.db import transaction
from django.db.models import Max
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action, api_view, permission_classes

from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.assessment.models import (
    MCQQuestion,
    MCQAttempt,
    PracticeQuestion,
    QuestionReport,
    QuizSession,
    QuizSessionQuestion,
    MCQOption,
)
from apps.assessment.models.quiz import SessionState
from apps.assessment.permissions import IsTeacherOrAdmin, IsOwnerOfSession
from apps.assessment.serializers.bank import (
    MCQQuestionSerializer,
    MCQQuestionPlaySerializer,
    MCQQuestionCreateSerializer,
    PracticeQuestionSerializer,
    PracticeQuestionCreateSerializer,
    QuestionReportSerializer,
    MCQGenerateInputSerializer,
)
from apps.assessment.serializers.quiz import (
    QuizStartSerializer,
    QuizSessionSerializer,
    QuizAnswerSerializer,
)
from apps.assessment.selectors import select_mcq_questions_for_session
from apps.assessment.services import apply_answer_to_session_question, finish_session_and_compute_result

from .services_openai import generate_mcqs



class MCQQuestionViewSet(viewsets.ModelViewSet):
    queryset = MCQQuestion.objects.all().prefetch_related("options")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return MCQQuestionCreateSerializer
        # Student-safe read serializer (no is_correct / explanation).
        return MCQQuestionPlaySerializer

    def get_permissions(self):
        # Authoring is staff-only; reading and the `answer` practice action are
        # open to any authenticated user.
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsTeacherOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)

        subject = self.request.query_params.get("subject")
        chapter = self.request.query_params.get("chapter")
        topic = self.request.query_params.get("topic")
        difficulty = self.request.query_params.get("difficulty")

        # Scope params are academics PKs (FK columns).
        if subject:
            qs = qs.filter(subject_id=subject)
        if chapter:
            qs = qs.filter(chapter_id=chapter)
        if topic:
            qs = qs.filter(topic_id=topic)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs

    @action(detail=True, methods=["post"], url_path="answer", permission_classes=[IsAuthenticated])
    def answer(self, request, pk=None):
        """Single-question practice (replaces the old mcq app endpoint).

        POST /api/assessment/mcq/questions/{id}/answer/  body: {"choice_id": N}
        """
        question = self.get_object()
        choice_id = request.data.get("choice_id")
        if not choice_id:
            return Response({"ok": False, "error": "choice_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            option = question.options.get(id=choice_id)
        except MCQOption.DoesNotExist:
            return Response({"ok": False, "error": "Invalid choice_id"}, status=status.HTTP_400_BAD_REQUEST)

        is_correct = bool(option.is_correct)
        last_no = (
            MCQAttempt.objects.filter(user=request.user, question=question).aggregate(m=Max("attempt_no"))["m"]
        ) or 0
        MCQAttempt.objects.create(
            user=request.user, question=question, selected_option=option,
            is_correct=is_correct, attempt_no=last_no + 1,
        )

        if is_correct:
            from apps.gamification.services.xp import award_xp
            award_xp(
                user=request.user,
                source="practice_correct",
                points=5,
                idempotency_key=f"practice_correct:{request.user.id}:{question.id}",
                object_type="mcq_question",
                object_id=str(question.id),
            )

        return Response({"is_correct": is_correct}, status=status.HTTP_200_OK)


class PracticeQuestionViewSet(viewsets.ModelViewSet):
    queryset = PracticeQuestion.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return PracticeQuestionCreateSerializer
        return PracticeQuestionSerializer

    def get_permissions(self):
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated(), IsTeacherOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)

        subject = self.request.query_params.get("subject")
        chapter = self.request.query_params.get("chapter")
        topic = self.request.query_params.get("topic")
        difficulty = self.request.query_params.get("difficulty")

        if subject:
            qs = qs.filter(subject=subject)
        if chapter:
            qs = qs.filter(chapter=chapter)
        if topic:
            qs = qs.filter(topic=topic)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs


class QuestionReportViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = QuestionReport.objects.all()
    serializer_class = QuestionReportSerializer
    permission_classes = [IsAuthenticated]


class QuizSessionViewSet(viewsets.GenericViewSet):
    queryset = QuizSession.objects.all().prefetch_related("session_questions", "session_questions__question", "session_questions__question__options")
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # object-level checks for session-specific actions
        if self.action in ["answer", "finish", "review"]:
            return [IsAuthenticated(), IsOwnerOfSession()]
        return [IsAuthenticated()]

    @action(detail=False, methods=["post"], url_path="start")
    def start(self, request):
        """
        POST /quizzes/start/ -> create session + select questions
        """
        s = QuizStartSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        data = s.validated_data
        scope = data.get("scope", {}) or {}
        count = data["count"]
        mode = data["mode"]
        difficulty_mix = data.get("difficulty_mix", {}) or {}

        subject = str(scope.get("subject", "")) if scope.get("subject") is not None else ""
        chapter = str(scope.get("chapter", "")) if scope.get("chapter") is not None else ""
        topic = str(scope.get("topic", "")) if scope.get("topic") is not None else ""

        with transaction.atomic():
            session = QuizSession.objects.create(
                user=request.user,
                mode=mode,
                state=SessionState.CREATED,
                subject=subject,
                chapter=chapter,
                topic=topic,
                requested_count=count,
                difficulty_mix=difficulty_mix,
            )
            session.mark_started()
            session.save(update_fields=["state", "started_at"])

            questions = select_mcq_questions_for_session(scope=scope, count=count, difficulty_mix=difficulty_mix)

            # create session questions
            objs = [
                QuizSessionQuestion(session=session, question=q, order=i)
                for i, q in enumerate(questions, start=1)
            ]
            QuizSessionQuestion.objects.bulk_create(objs)

        return Response(
            {
                "session": QuizSessionSerializer(session).data,
                "questions": self._serialize_session_questions_for_attempt(session),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="answer")
    def answer(self, request, pk=None):
        """
        POST /quizzes/{id}/answer/ -> store answer
        """
        session = self.get_object()
        self.check_object_permissions(request, session)

        s = QuizAnswerSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        sq = apply_answer_to_session_question(session, s.validated_data)
        return Response(
            {
                "ok": True,
                "question_id": sq.question_id,
                "is_correct": sq.is_correct,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="finish")
    def finish(self, request, pk=None):
        """
        POST /quizzes/{id}/finish/ -> compute score + call XP service
        """
        session = self.get_object()
        self.check_object_permissions(request, session)

        result = finish_session_and_compute_result(session)
        return Response(
            {
                "session": QuizSessionSerializer(session).data,
                "result": {
                    "total": result.total,
                    "correct": result.correct,
                    "score": result.score,
                    "percentage": result.percentage,
                    "xp_awarded": result.xp_awarded,
                },
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="review")
    def review(self, request, pk=None):
        """
        GET /quizzes/{id}/review/ -> show solutions/explanations (only after finish)
        """
        session = self.get_object()
        self.check_object_permissions(request, session)

        if session.state != SessionState.FINISHED:
            raise ValidationError("Review is only available after finishing the quiz.")

        result = getattr(session, "result", None)
        if not result:
            raise ValidationError("Result not found. Please finish again or contact support.")

        questions = []
        sqs = session.session_questions.all().select_related("question").prefetch_related("question__options")

        for sq in sqs:
            q = sq.question
            correct_option = q.options.filter(is_correct=True).first()
            questions.append(
                {
                    "question_id": q.id,
                    "title": q.title,
                    "question_text": q.question_text,
                    "explanation": q.explanation,
                    "selected_option_id": sq.selected_option_id,
                    "correct_option": {
                        "id": correct_option.id if correct_option else None,
                        "text": correct_option.text if correct_option else None,
                    },
                    "options": [{"id": o.id, "text": o.text} for o in q.options.all()],
                    "is_correct": sq.is_correct,
                    "time_spent_seconds": sq.time_spent_seconds,
                }
            )

        return Response(
            {
                "session": QuizSessionSerializer(session).data,
                "result": {
                    "total": result.total,
                    "correct": result.correct,
                    "score": result.score,
                    "percentage": result.percentage,
                    "xp_awarded": result.xp_awarded,
                },
                "questions": questions,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        """
        GET /quizzes/history/
        """
        qs = QuizSession.objects.filter(user=request.user).order_by("-id")[:100]
        data = QuizSessionSerializer(qs, many=True).data
        return Response({"items": data}, status=status.HTTP_200_OK)

    def _serialize_session_questions_for_attempt(self, session: QuizSession):
        """
        Return quiz questions WITHOUT correct answers.
        """
        sqs = session.session_questions.all().select_related("question").prefetch_related("question__options")
        out = []
        for sq in sqs:
            q = sq.question
            out.append(
                {
                    "id": q.id,
                    "title": q.title,
                    "question_text": q.question_text,
                    "difficulty": q.difficulty,
                    "subject": q.subject_id,
                    "chapter": q.chapter_id,
                    "topic": q.topic_id,
                    "order": sq.order,
                    "options": [{"id": o.id, "text": o.text} for o in q.options.all()],
                }
            )
        return out







@api_view(["POST"])
@permission_classes([IsAuthenticated, IsTeacherOrAdmin])
def generate_mcqs_api(request):
    # Paid AI call — restricted to staff/teachers (not any authenticated user).
    s = MCQGenerateInputSerializer(data=request.data)
    s.is_valid(raise_exception=True)

    try:
        data = generate_mcqs(**s.validated_data)
    except Exception as exc:  # provider/key/timeout errors must not 500 raw
        return Response(
            {"detail": "MCQ generation is currently unavailable.", "error": str(exc)},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    return Response(data)
