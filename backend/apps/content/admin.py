from django.contrib import admin
from .models import Note, Attachment, TopicResource, Bookmark, DownloadablePack

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "topic", "visibility", "created_by", "created_at")
    list_filter = ("visibility", "topic")
    search_fields = ("title", "content_richtext")

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "size", "uploaded_by", "created_at")
    list_filter = ("type",)
    search_fields = ("file",)

@admin.register(TopicResource)
class TopicResourceAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "resource_type", "note", "attachment", "url", "created_at")
    list_filter = ("resource_type", "topic")

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "entity_type", "entity_id", "created_at")
    list_filter = ("entity_type",)
    search_fields = ("user__username", "entity_id")

@admin.register(DownloadablePack)
class DownloadablePackAdmin(admin.ModelAdmin):
    list_display = ("id", "topic", "chapter", "version", "size", "created_at")
    list_filter = ("version",)
