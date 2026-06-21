from rest_framework import serializers
from .models import TopicProgress, DailyActivity, StudyStreak, WeakTopicCache, UserGoal, ProgressSnapshot

class TopicProgressSerializer(serializers.ModelSerializer):
    accuracy = serializers.FloatField(read_only=True)

    class Meta:
        model = TopicProgress
        fields = [
            "topic",
            "attempts", "correct", "total_answered",
            "easy_answered", "medium_answered", "hard_answered",
            "last_score", "last_total",
            "mastery", "confidence", "accuracy",
            "last_practiced_at",
            "next_review_at", "interval_days", "ease",
            "updated_at",
        ]

class DailyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivity
        fields = ["date", "minutes", "attempted", "correct", "xp_earned"]

class StudyStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyStreak
        fields = ["current_streak", "best_streak", "last_active_date"]

class WeakTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeakTopicCache
        fields = ["topic", "weakness_score", "computed_at"]

class DueTopicSerializer(serializers.ModelSerializer):
    accuracy = serializers.FloatField(read_only=True)

    class Meta:
        model = TopicProgress
        fields = ["topic", "mastery", "accuracy", "next_review_at", "interval_days"]

class UserGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGoal
        fields = ["daily_minutes_goal", "daily_attempt_goal", "weekly_topics_mastered_goal", "updated_at"]

class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressSnapshot
        fields = ["date", "topics", "total_answered", "accuracy", "avg_mastery"]

class DashboardSerializer(serializers.Serializer):
    today = DailyActivitySerializer()
    streak = StudyStreakSerializer()
    goals = UserGoalSerializer()
    totals = serializers.DictField()
    mastery_buckets = serializers.DictField()
    weak_topics = serializers.ListField()
    due_topics = serializers.ListField()
    activity_7d = serializers.ListField()
