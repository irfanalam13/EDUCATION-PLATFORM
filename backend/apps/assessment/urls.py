from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.assessment.views import (
    MCQQuestionViewSet,
    PracticeQuestionViewSet,
    QuestionReportViewSet,
    QuizSessionViewSet,
)
from .views import generate_mcqs_api



router = DefaultRouter()
router.register(r"mcq/questions", MCQQuestionViewSet, basename="mcq-questions")
router.register(r"practice/questions", PracticeQuestionViewSet, basename="practice-questions")
router.register(r"reports", QuestionReportViewSet, basename="question-reports")
router.register(r"quizzes", QuizSessionViewSet, basename="quiz-sessions")

urlpatterns = [
    path("", include(router.urls)),
    path("mcq/generate/", generate_mcqs_api),
]
