from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


User = settings.AUTH_USER_MODEL


def ai_document_upload_to(instance: "AIDocument", filename: str) -> str:
    now = timezone.now()
    return f"ai/user_{instance.user_id}/{now:%Y/%m}/{filename}"


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AIDocument(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_documents")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=ai_document_upload_to)
    mime_type = models.CharField(max_length=120, blank=True, default="")
    size = models.BigIntegerField(default=0)
    pages = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    error = models.TextField(blank=True, default="")
    extracted_text = models.TextField(blank=True, default="")
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status", "-created_at"]),
        ]

    def save(self, *args, **kwargs):
        try:
            if self.file and hasattr(self.file, "size") and self.file.size:
                self.size = int(self.file.size)
        except Exception:
            pass
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class AIKnowledgeChunk(TimeStampedModel):
    class SourceType(models.TextChoices):
        PDF = "pdf", "PDF"
        COURSE_TOPIC = "course_topic", "Course topic"
        COURSE_NOTE = "course_note", "Course note"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_chunks", null=True, blank=True)
    document = models.ForeignKey(AIDocument, on_delete=models.CASCADE, related_name="chunks", null=True, blank=True)
    source_type = models.CharField(max_length=32, choices=SourceType.choices, db_index=True)
    source_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    title = models.CharField(max_length=255, blank=True, default="")
    text = models.TextField()
    embedding = models.JSONField(default=list)
    embedding_model = models.CharField(max_length=80, blank=True, default="")
    token_count = models.PositiveIntegerField(default=0)
    page_start = models.PositiveIntegerField(null=True, blank=True)
    page_end = models.PositiveIntegerField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["source_type", "order", "id"]
        indexes = [
            models.Index(fields=["source_type", "source_id"]),
            models.Index(fields=["user", "source_type"]),
            models.Index(fields=["document", "order"]),
        ]

    def __str__(self) -> str:
        return f"{self.source_type}:{self.title or self.source_id}:{self.order}"


class AIChatSession(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_chat_sessions")
    title = models.CharField(max_length=255, blank=True, default="New chat")

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["user", "-updated_at"])]

    def __str__(self) -> str:
        return self.title


class AIChatMessage(TimeStampedModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    session = models.ForeignKey(AIChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    citations = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [models.Index(fields=["session", "created_at"])]

    def __str__(self) -> str:
        return f"{self.session_id}:{self.role}"
