from django.contrib import admin
from .models import Level, Stream, Subject, Chapter, Topic, Tag
from rest_framework.filters import SearchFilter, OrderingFilter


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "order", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("order", "id")


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "is_active", "created_at")
    list_filter = ("is_active",)
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ("name", "code")
    ordering = ("name",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "level", "stream", "order", "is_active")
    list_filter = ("level", "stream", "is_active")
    search_fields = ("name", "code")
    filter_backends = [SearchFilter, OrderingFilter]    
    ordering = ("level", "stream", "order", "id")
    autocomplete_fields = ("level", "stream")


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "subject", "number", "order", "is_active")
    list_filter = ("subject__level", "subject__stream", "is_active")
    filter_backends = [SearchFilter, OrderingFilter]

    search_fields = ("title", "subject__name")
    ordering = ("subject", "order", "number", "id")
    autocomplete_fields = ("subject",)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "chapter", "order", "is_active")
    list_filter = ("chapter__subject__level", "chapter__subject__stream", "is_active")
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ("title", "chapter__title", "chapter__subject__name", "content")
    ordering = ("chapter", "order", "id")
    autocomplete_fields = ("chapter",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
