from __future__ import annotations

from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_learning.models import StudyRecommendation, WeakTopic, StudyPlan
from apps.ai_learning.serializers import (
    StudyRecommendationSerializer, WeakTopicSerializer, StudyPlanSerializer,
)
from apps.ai_learning.services.mastery_calculator import (
    topic_mastery_rows, overall_mastery, band_distribution,
)
from apps.ai_learning.tasks import generate_all, mastery_cache_key
from apps.billing.features import FEATURE_AI_RECOMMENDATIONS, FEATURE_STUDY_PLANS
from apps.billing.permissions import requires_feature


class RecommendationsView(APIView):
    """GET /api/ai/recommendations/ — current pending recommendations."""
    permission_classes = [IsAuthenticated, requires_feature(FEATURE_AI_RECOMMENDATIONS)]

    def get(self, request):
        qs = (
            StudyRecommendation.objects.filter(
                user=request.user, status=StudyRecommendation.Status.PENDING
            )
            .select_related("topic")
            .order_by("-priority")
        )
        return Response(StudyRecommendationSerializer(qs, many=True).data)


class WeakTopicsView(APIView):
    """GET /api/ai/weak-topics/ — materialized weak topics with scores."""
    permission_classes = [IsAuthenticated, requires_feature(FEATURE_AI_RECOMMENDATIONS)]

    def get(self, request):
        qs = (
            WeakTopic.objects.filter(user=request.user)
            .select_related("topic")
            .order_by("-weak_score")
        )
        return Response(WeakTopicSerializer(qs, many=True).data)


class MasteryView(APIView):
    """GET /api/ai/mastery/ — per-topic mastery bands + overall + distribution."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        key = mastery_cache_key(request.user.id)
        data = cache.get(key)
        if data is None:
            rows = topic_mastery_rows(request.user)
            data = {
                "overall_mastery": overall_mastery(request.user),
                "band_distribution": band_distribution(rows),
                "topics": rows,
            }
            cache.set(key, data, 300)
        return Response(data)


class StudyPlanView(APIView):
    """GET /api/ai/study-plan/ — most recent plan with its timed sessions."""
    permission_classes = [IsAuthenticated, requires_feature(FEATURE_STUDY_PLANS)]

    def get(self, request):
        plan = (
            StudyPlan.objects.filter(user=request.user)
            .prefetch_related("sessions", "sessions__topic")
            .order_by("-date")
            .first()
        )
        if not plan:
            return Response({"plan": None, "detail": "No study plan yet — generate one."})
        return Response(StudyPlanSerializer(plan).data)


class GeneratePlanView(APIView):
    """POST /api/ai/generate-plan/ — run the engine and return today's plan.

    Runs the same pipeline the Celery task uses; synchronous so the client gets
    the plan immediately. `generate_for_user.delay()` is available for batch/cron.
    """
    permission_classes = [IsAuthenticated, requires_feature(FEATURE_STUDY_PLANS)]

    def post(self, request):
        result = generate_all(request.user, build_plan=True)
        plan = result["plan"]
        return Response(
            {
                "ok": True,
                "weak_topics": result["weak_count"],
                "recommendations": len(result["recs"]),
                "plan": StudyPlanSerializer(plan).data if plan else None,
            },
            status=status.HTTP_201_CREATED,
        )
