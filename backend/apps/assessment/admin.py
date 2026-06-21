from django.contrib import admin
from apps.assessment.models import (
    MCQQuestion, MCQOption, PracticeQuestion, QuestionReport,
    QuizTemplate, QuizSession, QuizSessionQuestion, QuizResult
)

class MCQOptionInline(admin.TabularInline):
    model = MCQOption
    extra = 2


@admin.register(MCQQuestion)
class MCQQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "subject", "chapter", "topic", "difficulty", "is_active", "created_at")
    list_filter = ("difficulty", "is_active", "subject", "chapter", "topic")
    search_fields = ("title", "question_text")
    inlines = [MCQOptionInline]


@admin.register(PracticeQuestion)
class PracticeQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "chapter", "topic", "difficulty", "is_active", "created_at")
    list_filter = ("difficulty", "is_active", "subject", "chapter", "topic")
    search_fields = ("prompt",)


@admin.register(QuestionReport)
class QuestionReportAdmin(admin.ModelAdmin):
    list_display = ("id", "question_type", "reason", "status", "created_at")
    list_filter = ("question_type", "status")
    search_fields = ("reason", "details")


@admin.register(QuizTemplate)
class QuizTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "count", "mode", "is_active", "created_at")
    list_filter = ("mode", "is_active")


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "mode", "state", "requested_count", "created_at", "finished_at")
    list_filter = ("mode", "state")
    search_fields = ("user__username", "user__email")


@admin.register(QuizSessionQuestion)
class QuizSessionQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "question", "order", "selected_option_id", "is_correct", "time_spent_seconds")
    list_filter = ("is_correct",)


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "total", "correct", "percentage", "xp_awarded", "computed_at")
