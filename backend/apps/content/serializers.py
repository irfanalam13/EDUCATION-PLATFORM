from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework import serializers

from .models import (
    Note, Attachment, TopicResource, Bookmark, DownloadablePack,
    NoteTag,
    Comment, Report,
    FlashcardDeck, Flashcard, FlashcardReview,
    QAQuestion, QAAnswer,
    Collection, CollectionItem
)


class NoteSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Note
        fields = ["id", "topic", "title", "content_richtext", "visibility", "created_by", "tags", "created_at", "updated_at"]

    def get_tags(self, obj):
        return [nt.tag.name for nt in obj.note_tags.select_related("tag").all()]


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attachment
        fields = ["id", "file", "file_url", "type", "size", "mime_type", "pages", "duration_sec", "uploaded_by", "created_at", "updated_at"]
        read_only_fields = ["size"]

    def get_file_url(self, obj):
        try:
            return obj.file.url if obj.file else ""
        except Exception:
            return ""


class TopicResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicResource
        fields = ["id", "topic", "resource_type", "note", "attachment", "url", "created_at", "updated_at"]

    def validate(self, attrs):
        resource_type = attrs.get("resource_type", getattr(self.instance, "resource_type", None))
        note = attrs.get("note", getattr(self.instance, "note", None))
        attachment = attrs.get("attachment", getattr(self.instance, "attachment", None))
        url = attrs.get("url", getattr(self.instance, "url", ""))

        if resource_type == "note":
            if not note:
                raise serializers.ValidationError({"note": "note is required when resource_type='note'."})
            if attachment or url:
                raise serializers.ValidationError("For NOTE resource, only note should be set.")
        elif resource_type == "attachment":
            if not attachment:
                raise serializers.ValidationError({"attachment": "attachment is required when resource_type='attachment'."})
            if note or url:
                raise serializers.ValidationError("For ATTACHMENT resource, only attachment should be set.")
        elif resource_type in ("link", "video"):
            if not url:
                raise serializers.ValidationError({"url": "url is required when resource_type is 'link' or 'video'."})
            if note or attachment:
                raise serializers.ValidationError("For LINK/VIDEO resource, only url should be set.")
        return attrs


class BookmarkSerializer(serializers.ModelSerializer):
    entity_app_label = serializers.CharField(write_only=True)
    entity_model = serializers.CharField(write_only=True)

    class Meta:
        model = Bookmark
        fields = ["id", "user", "entity_type", "entity_id", "entity_app_label", "entity_model", "created_at", "updated_at"]
        read_only_fields = ["user", "entity_type"]

    def create(self, validated_data):
        app_label = validated_data.pop("entity_app_label")
        model = validated_data.pop("entity_model")
        entity_id = validated_data["entity_id"]

        try:
            ct = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError({"entity_model": "Invalid entity type."})

        return Bookmark.objects.create(
            user=self.context["request"].user,
            entity_type=ct,
            entity_id=entity_id,
        )


class DownloadablePackSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DownloadablePack
        fields = ["id", "topic", "chapter", "version", "size", "checksum", "status", "file", "file_url", "created_at", "updated_at"]
        read_only_fields = ["size", "checksum", "status"]

    def get_file_url(self, obj):
        try:
            return obj.file.url if obj.file else ""
        except Exception:
            return ""


# -------- Tagging (Tag owned by academics) --------
class NoteTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteTag
        fields = ["id", "note", "tag", "created_at", "updated_at"]




# -------- Comments --------
class CommentSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Comment
        fields = ["id", "user", "topic", "note", "resource", "parent", "content", "created_at", "updated_at"]


class ReportSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Report
        fields = ["id", "user", "topic", "note", "resource", "reason", "detail", "status", "created_at", "updated_at"]
        read_only_fields = ["status"]


# -------- Flashcards + SRS --------
class FlashcardDeckSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = FlashcardDeck
        fields = ["id", "topic", "title", "created_by", "created_at", "updated_at"]


class FlashcardSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Flashcard
        fields = ["id", "deck", "front", "back", "created_by", "created_at", "updated_at"]


class FlashcardReviewSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = FlashcardReview
        fields = ["id", "user", "card", "ease", "interval_days", "due_at", "created_at", "updated_at"]
        read_only_fields = ["ease", "interval_days", "due_at"]

    def create(self, validated_data):
        # initialize review row if needed
        obj, _ = FlashcardReview.objects.get_or_create(
            user=validated_data["user"],
            card=validated_data["card"],
            defaults={"ease": 2.50, "interval_days": 0, "due_at": timezone.now()},
        )
        return obj


class FlashcardGradeSerializer(serializers.Serializer):
    """
    grade: 0..3 (0=again,1=hard,2=good,3=easy)
    """
    card = serializers.IntegerField()
    grade = serializers.IntegerField(min_value=0, max_value=3)


# -------- Q&A --------
class QAQuestionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = QAQuestion
        fields = ["id", "topic", "user", "title", "body", "is_resolved", "created_at", "updated_at"]
        read_only_fields = ["is_resolved"]  # set only via the /resolve/ action


class QAAnswerSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = QAAnswer
        fields = ["id", "question", "user", "body", "is_accepted", "created_at", "updated_at"]
        read_only_fields = ["is_accepted"]  # set only via the /accept/ action


# -------- Collections --------
class CollectionSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Collection
        fields = ["id", "topic", "title", "description", "created_by", "is_published", "created_at", "updated_at"]


class CollectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionItem
        fields = ["id", "collection", "order", "note", "resource", "attachment", "url", "created_at", "updated_at"]
