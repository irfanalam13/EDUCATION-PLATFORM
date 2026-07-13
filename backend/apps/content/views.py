from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
)
from rest_framework.response import Response

from .models import (
    Note, Attachment, TopicResource, Bookmark, DownloadablePack,
    NoteTag,
    Comment, Report,
    FlashcardDeck, Flashcard, FlashcardReview,
    QAQuestion, QAAnswer,
    Collection, CollectionItem
)
from .serializers import (
    NoteSerializer, AttachmentSerializer, TopicResourceSerializer,
    BookmarkSerializer, DownloadablePackSerializer,
    NoteTagSerializer,
    CommentSerializer, ReportSerializer,
    FlashcardDeckSerializer, FlashcardSerializer, FlashcardReviewSerializer, FlashcardGradeSerializer,
    QAQuestionSerializer, QAAnswerSerializer,
    CollectionSerializer, CollectionItemSerializer
)
from .permissions import (
    IsOwnerOrReadByVisibility,
    IsUploaderOrReadOnly,
    IsCreatorOrReadOnly,
    IsNoteOwnerOrReadOnly,
    IsCollectionOwnerOrReadOnly,
)


class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.select_related("topic", "created_by").all().order_by("-created_at")
    serializer_class = NoteSerializer
    permission_classes = [IsOwnerOrReadByVisibility]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["topic", "visibility", "created_by"]
    search_fields = ["title", "content_richtext"]
    ordering_fields = ["created_at", "title", "visibility"]

    def get_queryset(self):
        qs = Note.objects.select_related("topic", "created_by").all().order_by("-created_at")
        user = self.request.user
        # Private notes are only visible to their owner; public/unlisted to all.
        if user.is_authenticated:
            return qs.filter(Q(visibility__in=["public", "unlisted"]) | Q(created_by=user))
        return qs.filter(visibility__in=["public", "unlisted"])

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.select_related("uploaded_by").all().order_by("-created_at")
    serializer_class = AttachmentSerializer
    permission_classes = [IsUploaderOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["type", "uploaded_by"]
    ordering_fields = ["created_at", "size", "type"]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class TopicResourceViewSet(viewsets.ModelViewSet):
    queryset = TopicResource.objects.select_related("topic", "note", "attachment").all().order_by("-created_at")
    serializer_class = TopicResourceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["topic", "resource_type"]
    ordering_fields = ["created_at", "resource_type"]


class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).order_by("-created_at")


class DownloadablePackViewSet(viewsets.ModelViewSet):
    queryset = DownloadablePack.objects.select_related("topic", "chapter").all().order_by("-created_at")
    serializer_class = DownloadablePackSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["topic", "chapter", "version", "status"]
    ordering_fields = ["created_at", "size", "version"]


# ---- Tagging ----
class NoteTagViewSet(viewsets.ModelViewSet):
    queryset = NoteTag.objects.select_related("note", "tag").all().order_by("-created_at")
    serializer_class = NoteTagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsNoteOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["note", "tag"]



# ---- Comments + Reports ----
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related("user", "topic", "note", "resource", "parent").all().order_by("-created_at")
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["topic", "note", "resource", "parent"]
    ordering_fields = ["created_at"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["topic", "note", "resource", "status"]

    def get_queryset(self):
        # Abuse reports are private: a user sees only their own; staff see all.
        qs = Report.objects.select_related("user", "topic", "note", "resource").order_by("-created_at")
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ---- Flashcards + SRS ----
class FlashcardDeckViewSet(viewsets.ModelViewSet):
    queryset = FlashcardDeck.objects.select_related("topic", "created_by").all().order_by("-created_at")
    serializer_class = FlashcardDeckSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["topic", "created_by"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FlashcardViewSet(viewsets.ModelViewSet):
    queryset = Flashcard.objects.select_related("deck", "created_by").all().order_by("-created_at")
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["deck", "created_by"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FlashcardReviewViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["card"]

    def get_queryset(self):
        return FlashcardReview.objects.filter(user=self.request.user).select_related("card", "card__deck")

    @action(detail=False, methods=["get"], url_path="due")
    def due(self, request):
        now = timezone.now()
        qs = self.get_queryset().filter(due_at__lte=now).order_by("due_at")[:50]
        return Response(FlashcardReviewSerializer(qs, many=True).data)

    @action(detail=False, methods=["post"], url_path="grade")
    def grade(self, request):
        """
        grade: 0..3 (again/hard/good/easy)
        Minimal SM-2-ish update.
        """
        ser = FlashcardGradeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        card_id = ser.validated_data["card"]
        grade = ser.validated_data["grade"]

        review, _ = FlashcardReview.objects.get_or_create(
            user=request.user, card_id=card_id,
            defaults={"ease": 2.50, "interval_days": 0, "due_at": timezone.now()}
        )

        ease = float(review.ease)
        interval = int(review.interval_days)

        if grade == 0:
            interval = 1
            ease = max(1.3, ease - 0.2)
        elif grade == 1:
            interval = max(1, int(interval * 1.2))
            ease = max(1.3, ease - 0.05)
        elif grade == 2:
            interval = 2 if interval == 0 else int(interval * ease)
        else:  # 3
            interval = 3 if interval == 0 else int(interval * (ease + 0.15))
            ease = min(3.0, ease + 0.05)

        review.ease = round(ease, 2)
        review.interval_days = max(1, interval)
        review.due_at = timezone.now() + timezone.timedelta(days=review.interval_days)
        review.save()

        return Response(FlashcardReviewSerializer(review).data, status=status.HTTP_200_OK)


# ---- Q&A ----
class QAQuestionViewSet(viewsets.ModelViewSet):
    queryset = QAQuestion.objects.select_related("topic", "user").all().order_by("-created_at")
    serializer_class = QAQuestionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["topic", "is_resolved", "user"]
    search_fields = ["title", "body"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        # get_object() enforces IsCreatorOrReadOnly for unsafe methods, so only
        # the question's author can resolve it.
        question = self.get_object()
        question.is_resolved = True
        question.save(update_fields=["is_resolved", "updated_at"])
        return Response(QAQuestionSerializer(question).data)


class QAAnswerViewSet(viewsets.ModelViewSet):
    queryset = QAAnswer.objects.select_related("question", "user").all().order_by("-created_at")
    serializer_class = QAAnswerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["question", "user", "is_accepted"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        # Accepting an answer is the QUESTION author's action (not the answer
        # author's), so we bypass the object-owner check and verify ownership of
        # the parent question explicitly.
        answer = QAAnswer.objects.select_related("question").filter(pk=pk).first()
        if not answer:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if answer.question.user_id != request.user.id:
            return Response(
                {"detail": "Only the question author can accept an answer."},
                status=status.HTTP_403_FORBIDDEN,
            )
        answer.is_accepted = True
        answer.save(update_fields=["is_accepted", "updated_at"])
        # Only one accepted answer per question.
        QAAnswer.objects.filter(question=answer.question).exclude(pk=answer.pk).update(is_accepted=False)
        return Response(QAAnswerSerializer(answer).data)


# ---- Collections ----
class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["topic", "created_by", "is_published"]
    search_fields = ["title", "description"]

    def get_queryset(self):
        # Unpublished collections are visible only to their owner.
        qs = Collection.objects.select_related("topic", "created_by").order_by("-created_at")
        user = self.request.user
        if user.is_authenticated:
            return qs.filter(Q(is_published=True) | Q(created_by=user))
        return qs.filter(is_published=True)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CollectionItemViewSet(viewsets.ModelViewSet):
    queryset = CollectionItem.objects.select_related("collection", "note", "resource", "attachment").all().order_by("order")
    serializer_class = CollectionItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsCollectionOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["collection"]
