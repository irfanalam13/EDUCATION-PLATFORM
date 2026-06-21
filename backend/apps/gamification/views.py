# apps/gamification/views.py
from __future__ import annotations

from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.cache import cache
from django.utils import timezone

from apps.gamification.models import (
    UserGamificationProfile, XpTransaction, Badge,
    Quest, UserQuestProgress
)
from apps.gamification.permissions import IsOwner
from apps.gamification.serializers import (
    GamificationProfileSerializer, XpTransactionSerializer,
    BadgeSerializer, LeaderboardSerializer,
    UserQuestProgressSerializer
)
from apps.gamification.selectors import get_leaderboard
from apps.gamification.services.streaks import touch_activity
from apps.gamification.services.quests import claim_quest


class GamificationProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="profile")
    def profile(self, request):
        profile, _ = UserGamificationProfile.objects.get_or_create(user=request.user)
        return Response(GamificationProfileSerializer(profile).data)

    @action(detail=False, methods=["post"], url_path="touch")
    def touch(self, request):
        profile = touch_activity(request.user)
        return Response({"ok": True, "streak_days": profile.streak_days, "last_active_date": str(profile.last_active_date)})


class XpTransactionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = XpTransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return XpTransaction.objects.filter(user=self.request.user).order_by("-created_at")


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all().order_by("code")
    serializer_class = BadgeSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]


class LeaderboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        scope = request.query_params.get("scope", "global")
        period = request.query_params.get("period", "weekly")
        scope_id = request.query_params.get("scope_id", "")
        # Validate + cap the limit so a client can't request an unbounded scan.
        try:
            limit = int(request.query_params.get("limit", 50))
        except (TypeError, ValueError):
            limit = 50
        limit = max(1, min(limit, 100))

        # Short cache: leaderboards only change when XP is awarded + recomputed.
        cache_key = f"lb:{scope}:{scope_id}:{period}:{limit}"
        data = cache.get(cache_key)
        if data is None:
            entries = get_leaderboard(scope=scope, period=period, scope_id=scope_id, limit=limit)
            data = LeaderboardSerializer(entries, many=True).data
            cache.set(cache_key, data, timeout=30)
        return Response(data)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        scope = request.query_params.get("scope", "global")
        period = request.query_params.get("period", "weekly")
        scope_id = request.query_params.get("scope_id", "")

        entries = list(get_leaderboard(scope=scope, period=period, scope_id=scope_id, limit=200))
        # find user rank in this slice
        rank = None
        for i, e in enumerate(entries, start=1):
            if e.user_id == request.user.id:
                rank = i
                break
        return Response({
            "ok": True,
            "rank_in_top200": rank,
            "count_considered": len(entries),
        })


class QuestProgressViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        qs = UserQuestProgress.objects.filter(user=request.user).select_related("quest").order_by("-updated_at")
        return Response(UserQuestProgressSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path=r"claim/(?P<code>[-a-zA-Z0-9_]+)")
    def claim(self, request, code=None):
        quest = Quest.objects.filter(code=code, is_active=True).first()
        if not quest:
            return Response({"ok": False, "reason": "quest_not_found"}, status=404)
        result = claim_quest(request.user, quest)
        status_code = 200 if result.get("ok") else 400
        return Response(result, status=status_code)
