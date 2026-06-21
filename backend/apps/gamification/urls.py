# apps/gamification/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.gamification.views import (
    GamificationProfileViewSet,
    XpTransactionViewSet,
    BadgeViewSet,
    LeaderboardViewSet,
    QuestProgressViewSet,
)

router = DefaultRouter()
router.register(r"gamification", GamificationProfileViewSet, basename="gamification")
router.register(r"xp-transactions", XpTransactionViewSet, basename="xp-transactions")
router.register(r"badges", BadgeViewSet, basename="badges")
router.register(r"leaderboards", LeaderboardViewSet, basename="leaderboards")
router.register(r"quests", QuestProgressViewSet, basename="quests")

urlpatterns = [
    path("", include(router.urls)),
]
