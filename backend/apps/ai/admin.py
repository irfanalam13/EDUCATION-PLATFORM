from django.contrib import admin

from .models import AIDocument, AIChatMessage, AIChatSession, AIKnowledgeChunk


@admin.register(AIDocument)
class AIDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "status", "pages", "size", "processed_at", "created_at")
    list_filter = ("status", "created_at", "processed_at")
    search_fields = ("title", "user__email", "extracted_text")
    readonly_fields = ("size", "pages", "status", "error", "extracted_text", "processed_at", "created_at", "updated_at")


@admin.register(AIKnowledgeChunk)
class AIKnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "source_type", "source_id", "user", "document", "token_count", "created_at")
    list_filter = ("source_type", "embedding_model", "created_at")
    search_fields = ("title", "text", "source_id", "user__email")
    readonly_fields = ("embedding", "created_at", "updated_at")


class AIChatMessageInline(admin.TabularInline):
    model = AIChatMessage
    extra = 0
    readonly_fields = ("role", "content", "citations", "metadata", "created_at", "updated_at")
    can_delete = False


@admin.register(AIChatSession)
class AIChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "updated_at", "created_at")
    search_fields = ("title", "user__email", "messages__content")
    inlines = [AIChatMessageInline]


@admin.register(AIChatMessage)
class AIChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("content", "session__title", "session__user__email")
