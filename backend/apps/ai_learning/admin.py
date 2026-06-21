from django.contrib import admin

from apps.ai_learning.models import (
    LearningProfile, WeakTopic, StudyRecommendation, StudyPlan, StudySession, RecommendationLog,
)


@admin.register(LearningProfile)
class LearningProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "overall_mastery", "topics_tracked", "weak_topic_count", "pace", "last_computed_at")
    search_fields = ("user__username",)


@admin.register(WeakTopic)
class WeakTopicAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "weak_score", "band", "computed_at")
    list_filter = ("band",)
    search_fields = ("user__username", "topic__title")


@admin.register(StudyRecommendation)
class StudyRecommendationAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "title", "priority", "status", "created_at")
    list_filter = ("kind", "status")


class StudySessionInline(admin.TabularInline):
    model = StudySession
    extra = 0


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "total_minutes", "status", "generated_at")
    inlines = [StudySessionInline]


@admin.register(RecommendationLog)
class RecommendationLogAdmin(admin.ModelAdmin):
    list_display = ("user", "source", "created_at")
