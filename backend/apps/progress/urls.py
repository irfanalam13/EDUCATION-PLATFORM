from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TopicProgressViewSet, DailyActivityViewSet, ProgressViewSet, GoalViewSet, SnapshotViewSet

router = DefaultRouter()
router.register(r"topics", TopicProgressViewSet, basename="progress-topics")
router.register(r"activity/daily", DailyActivityViewSet, basename="daily-activity")
router.register(r"goals", GoalViewSet, basename="progress-goals")
router.register(r"snapshots", SnapshotViewSet, basename="progress-snapshots")

progress = ProgressViewSet.as_view({"get": "dashboard"})
due = ProgressViewSet.as_view({"get": "due_topics"})
recs = TopicProgressViewSet.as_view({"get": "recommendations"})

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", progress, name="progress-dashboard"),
    path("due-topics/", due, name="due-topics"),
    path("recommendations/", recs, name="progress-recommendations"),
]
