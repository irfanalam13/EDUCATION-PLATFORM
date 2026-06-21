from rest_framework import serializers

from apps.ai_learning.models import (
    LearningProfile, WeakTopic, StudyRecommendation, StudyPlan, StudySession,
)


class LearningProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningProfile
        fields = [
            "overall_mastery", "topics_tracked", "weak_topic_count", "pace",
            "preferred_study_time", "daily_minutes_target", "last_computed_at",
        ]


class WeakTopicSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source="topic.title", read_only=True)

    class Meta:
        model = WeakTopic
        fields = ["topic", "topic_title", "weak_score", "mastery", "accuracy", "band", "reason", "computed_at"]


class StudyRecommendationSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source="topic.title", read_only=True, default=None)

    class Meta:
        model = StudyRecommendation
        fields = ["id", "topic", "topic_title", "kind", "title", "message", "priority", "status", "created_at"]


class StudySessionSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source="topic.title", read_only=True, default=None)

    class Meta:
        model = StudySession
        fields = ["id", "topic", "topic_title", "order", "start_time", "duration_min", "activity_type", "title", "completed"]


class StudyPlanSerializer(serializers.ModelSerializer):
    sessions = StudySessionSerializer(many=True, read_only=True)

    class Meta:
        model = StudyPlan
        fields = ["id", "date", "total_minutes", "status", "generated_at", "sessions"]
