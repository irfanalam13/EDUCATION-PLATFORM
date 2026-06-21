from django.conf import settings
from rest_framework import serializers

from .models import AIDocument, AIChatMessage, AIChatSession


class AIDocumentSerializer(serializers.ModelSerializer):
    chunk_count = serializers.IntegerField(source="chunks.count", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = AIDocument
        fields = [
            "id",
            "title",
            "file",
            "file_url",
            "mime_type",
            "size",
            "pages",
            "status",
            "error",
            "chunk_count",
            "processed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["mime_type", "size", "pages", "status", "error", "processed_at"]
        extra_kwargs = {
            "title": {"required": False, "allow_blank": True},
            "file": {"write_only": True},
        }

    def validate_file(self, value):
        content_type = (getattr(value, "content_type", "") or "").lower()
        filename = (getattr(value, "name", "") or "").lower()
        allowed_types = {"application/pdf", "application/x-pdf", ""}
        if content_type not in allowed_types or not filename.endswith(".pdf"):
            raise serializers.ValidationError("Only PDF uploads are supported for RAG documents.")

        max_mb = int(getattr(settings, "AI_MAX_UPLOAD_MB", 20))
        max_bytes = max_mb * 1024 * 1024
        if getattr(value, "size", 0) and value.size > max_bytes:
            raise serializers.ValidationError(f"PDF is too large. Maximum size is {max_mb} MB.")
        return value

    def get_file_url(self, obj):
        try:
            return obj.file.url if obj.file else ""
        except Exception:
            return ""


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIChatMessage
        fields = ["id", "role", "content", "citations", "metadata", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AIChatSession
        fields = ["id", "title", "messages", "created_at", "updated_at"]


class ChatSessionListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AIChatSession
        fields = ["id", "title", "last_message", "created_at", "updated_at"]

    def get_last_message(self, obj):
        message = obj.messages.order_by("-created_at", "-id").first()
        if not message:
            return None
        return ChatMessageSerializer(message).data


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False, trim_whitespace=True)
    session_id = serializers.IntegerField(required=False, allow_null=True)


class ChatResponseSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
    answer = serializers.CharField()
    source = serializers.CharField()
    citations = serializers.ListField(child=serializers.DictField(), default=list)
    message = ChatMessageSerializer()
