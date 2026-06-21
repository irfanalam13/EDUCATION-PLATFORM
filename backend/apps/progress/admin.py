from django.contrib import admin
from .models import TopicProgress, DailyActivity, StudyStreak, WeakTopicCache, UserGoal, ProgressSnapshot

@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "mastery", "confidence", "total_answered", "next_review_at", "updated_at")
    search_fields = ("user__username", "topic__title")
    list_filter = ("updated_at",)

admin.site.register(DailyActivity)
admin.site.register(StudyStreak)
admin.site.register(WeakTopicCache)
admin.site.register(UserGoal)
admin.site.register(ProgressSnapshot)
