# apps/gamification/serializers.py
from __future__ import annotations

from rest_framework import serializers

from apps.gamification.models import (
    UserGamificationProfile, XpTransaction, Badge, UserBadge,
    LeaderboardEntry, Quest, UserQuestProgress
)


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["id", "code", "name", "description", "icon", "is_active", "criteria"]


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ["id", "badge", "awarded_at", "metadata"]


class GamificationProfileSerializer(serializers.ModelSerializer):
    badges = serializers.SerializerMethodField()

    class Meta:
        model = UserGamificationProfile
        fields = ["level", "total_xp", "streak_days", "longest_streak", "freeze_tokens", "badges"]

    def get_badges(self, obj):
        qs = obj.user.badges.select_related("badge").order_by("-awarded_at")
        return UserBadgeSerializer(qs, many=True).data


class XpTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = XpTransaction
        fields = [
            "id", "created_at", "source",
            "object_type", "object_id",
            "points_base", "multiplier", "points_awarded",
            "status", "metadata",
        ]


class LeaderboardSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaderboardEntry
        fields = [
            "user_id", "username", "display_name",
            "scope", "scope_id", "period", "period_key", "xp_total", "updated_at",
        ]

    def get_display_name(self, obj):
        u = obj.user
        full = f"{u.first_name} {u.last_name}".strip()
        return full or u.username


class QuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quest
        fields = ["id", "code", "name", "description", "rules", "reward", "start_at", "end_at", "is_active"]


class UserQuestProgressSerializer(serializers.ModelSerializer):
    quest = QuestSerializer(read_only=True)

    class Meta:
        model = UserQuestProgress
        fields = ["id", "quest", "progress", "is_completed", "is_claimed", "updated_at"]
