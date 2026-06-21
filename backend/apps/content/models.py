from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

User = settings.AUTH_USER_MODEL

# NOTE: This app owns user-generated content only. The curriculum hierarchy
# (Subject → Chapter → Topic) and Tag are owned by the academics app; content
# references them by FK. There is no content.Topic / content.Chapter / content.Tag.


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# -----------------------
# Content: Notes / Attachments / Resources
# -----------------------
class Note(TimeStampedModel):
    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        UNLISTED = "unlisted", "Unlisted"
        PRIVATE = "private", "Private"

    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=255)
    content_richtext = models.TextField()
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PRIVATE, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")

    def __str__(self) -> str:
        return self.title


def attachment_upload_to(instance: "Attachment", filename: str) -> str:
    user_id = instance.uploaded_by_id or "anon"
    now = timezone.now()
    return f"attachments/user_{user_id}/{now:%Y/%m}/{filename}"


class Attachment(TimeStampedModel):
    class Type(models.TextChoices):
        PDF = "pdf", "PDF"
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio"
        VIDEO = "video", "Video"
        OTHER = "other", "Other"

    file = models.FileField(upload_to=attachment_upload_to)
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.OTHER, db_index=True)
    size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True, default="")
    pages = models.PositiveIntegerField(default=0)
    duration_sec = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attachments")

    def save(self, *args, **kwargs):
        try:
            if self.file and hasattr(self.file, "size") and self.file.size:
                self.size = int(self.file.size)
        except Exception:
            pass
        return super().save(*args, **kwargs)


class TopicResource(TimeStampedModel):
    class ResourceType(models.TextChoices):
        NOTE = "note", "Note"
        VIDEO = "video", "Video"
        LINK = "link", "Link"
        ATTACHMENT = "attachment", "Attachment"

    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="resources")
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices, db_index=True)

    note = models.ForeignKey(Note, on_delete=models.SET_NULL, null=True, blank=True, related_name="topic_resources")
    attachment = models.ForeignKey(
        Attachment, on_delete=models.SET_NULL, null=True, blank=True, related_name="topic_resources"
    )
    url = models.URLField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["topic", "resource_type"])]

    def clean(self):
        t = self.resource_type
        if t == self.ResourceType.NOTE:
            if not self.note_id:
                raise ValidationError({"note": "note is required when resource_type='note'."})
            if self.attachment_id or self.url:
                raise ValidationError("For NOTE resource, only note should be set.")
        elif t == self.ResourceType.ATTACHMENT:
            if not self.attachment_id:
                raise ValidationError({"attachment": "attachment is required when resource_type='attachment'."})
            if self.note_id or self.url:
                raise ValidationError("For ATTACHMENT resource, only attachment should be set.")
        elif t in (self.ResourceType.LINK, self.ResourceType.VIDEO):
            if not self.url:
                raise ValidationError({"url": "url is required when resource_type is 'link' or 'video'."})
            if self.note_id or self.attachment_id:
                raise ValidationError("For LINK/VIDEO resource, only url should be set.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


# -----------------------
# Bookmarks (generic)
# -----------------------
class Bookmark(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    entity_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    entity_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("entity_type", "entity_id")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "entity_type", "entity_id"], name="uniq_user_bookmark_entity"),
        ]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]


# -----------------------
# Downloadable packs (offline)
# -----------------------
def pack_upload_to(instance: "DownloadablePack", filename: str) -> str:
    now = timezone.now()
    return f"packs/{now:%Y/%m}/{filename}"


class DownloadablePack(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    topic = models.ForeignKey(
        "academics.Topic", on_delete=models.SET_NULL, null=True, blank=True, related_name="download_packs"
    )
    chapter = models.ForeignKey(
        "academics.Chapter", on_delete=models.SET_NULL, null=True, blank=True, related_name="download_packs"
    )
    version = models.CharField(max_length=50)
    size = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=128, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    file = models.FileField(upload_to=pack_upload_to, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(topic__isnull=False) & Q(chapter__isnull=True))
                    | (Q(topic__isnull=True) & Q(chapter__isnull=False))
                ),
                name="pack_requires_exactly_one_of_topic_or_chapter",
            ),
            models.UniqueConstraint(fields=["topic", "version"], name="uniq_pack_topic_version"),
            models.UniqueConstraint(fields=["chapter", "version"], name="uniq_pack_chapter_version"),
        ]


# -----------------------
# Tagging (Tag is owned by academics)
# -----------------------
class NoteTag(TimeStampedModel):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="note_tags")
    tag = models.ForeignKey("academics.Tag", on_delete=models.CASCADE, related_name="tag_notes")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["note", "tag"], name="uniq_note_tag"),
        ]


# -----------------------
# Comments + Reports
# -----------------------
class Comment(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="comments")
    note = models.ForeignKey(Note, null=True, blank=True, on_delete=models.CASCADE, related_name="comments")
    resource = models.ForeignKey(TopicResource, null=True, blank=True, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    content = models.TextField()

    class Meta:
        indexes = [models.Index(fields=["topic", "created_at"])]

    def clean(self):
        if not self.note_id and not self.resource_id:
            raise ValidationError("Comment must reference note or resource.")
        if self.note_id and self.resource_id:
            raise ValidationError("Comment cannot reference both note and resource.")


class Report(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWED = "reviewed", "Reviewed"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reports")
    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="reports")
    note = models.ForeignKey(Note, null=True, blank=True, on_delete=models.CASCADE, related_name="reports")
    resource = models.ForeignKey(TopicResource, null=True, blank=True, on_delete=models.CASCADE, related_name="reports")
    reason = models.CharField(max_length=100)
    detail = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)

    def clean(self):
        if not self.note_id and not self.resource_id:
            raise ValidationError("Report must reference note or resource.")
        if self.note_id and self.resource_id:
            raise ValidationError("Report cannot reference both note and resource.")


# -----------------------
# Flashcards + SRS
# -----------------------
class FlashcardDeck(TimeStampedModel):
    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="decks")
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="decks")

    def __str__(self) -> str:
        return self.title


class Flashcard(TimeStampedModel):
    deck = models.ForeignKey(FlashcardDeck, on_delete=models.CASCADE, related_name="cards")
    front = models.TextField()
    back = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cards")


class FlashcardReview(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="card_reviews")
    card = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name="reviews")

    ease = models.DecimalField(max_digits=4, decimal_places=2, default=2.50)
    interval_days = models.PositiveIntegerField(default=0)
    due_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "card"], name="uniq_user_card_review")
        ]


# -----------------------
# Q&A
# -----------------------
class QAQuestion(TimeStampedModel):
    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="qa_questions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="qa_questions")
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_resolved = models.BooleanField(default=False)


class QAAnswer(TimeStampedModel):
    question = models.ForeignKey(QAQuestion, on_delete=models.CASCADE, related_name="answers")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="qa_answers")
    body = models.TextField()
    is_accepted = models.BooleanField(default=False)


# -----------------------
# Teacher collections / playlists
# -----------------------
class Collection(TimeStampedModel):
    topic = models.ForeignKey("academics.Topic", on_delete=models.CASCADE, related_name="collections")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="collections")
    is_published = models.BooleanField(default=False)


class CollectionItem(TimeStampedModel):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="items")
    order = models.PositiveIntegerField(default=0)

    note = models.ForeignKey(Note, null=True, blank=True, on_delete=models.SET_NULL)
    resource = models.ForeignKey(TopicResource, null=True, blank=True, on_delete=models.SET_NULL)
    attachment = models.ForeignKey(Attachment, null=True, blank=True, on_delete=models.SET_NULL)
    url = models.URLField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["collection", "order"])]

    def clean(self):
        count = sum([1 if self.note_id else 0, 1 if self.resource_id else 0, 1 if self.attachment_id else 0, 1 if self.url else 0])
        if count != 1:
            raise ValidationError("CollectionItem must reference exactly one of note/resource/attachment/url.")
