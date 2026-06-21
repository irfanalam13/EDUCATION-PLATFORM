from django.urls import path

from apps.ai_learning.views import (
    RecommendationsView,
    WeakTopicsView,
    MasteryView,
    StudyPlanView,
    GeneratePlanView,
)

urlpatterns = [
    path("recommendations/", RecommendationsView.as_view(), name="ai-recommendations"),
    path("weak-topics/", WeakTopicsView.as_view(), name="ai-weak-topics"),
    path("mastery/", MasteryView.as_view(), name="ai-mastery"),
    path("study-plan/", StudyPlanView.as_view(), name="ai-study-plan"),
    path("generate-plan/", GeneratePlanView.as_view(), name="ai-generate-plan"),
]
