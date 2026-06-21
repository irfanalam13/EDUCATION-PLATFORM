from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    NoteViewSet, AttachmentViewSet, TopicResourceViewSet,
    BookmarkViewSet, DownloadablePackViewSet,
    NoteTagViewSet,
    CommentViewSet, ReportViewSet,
    FlashcardDeckViewSet, FlashcardViewSet, FlashcardReviewViewSet,
    QAQuestionViewSet, QAAnswerViewSet,
    CollectionViewSet, CollectionItemViewSet
)

router = DefaultRouter()
router.register(r"notes", NoteViewSet, basename="notes")
router.register(r"attachments", AttachmentViewSet, basename="attachments")
router.register(r"topic-resources", TopicResourceViewSet, basename="topic-resources")

router.register(r"bookmarks", BookmarkViewSet, basename="bookmarks")
router.register(r"download-packs", DownloadablePackViewSet, basename="download-packs")

router.register(r"note-tags", NoteTagViewSet, basename="note-tags")

router.register(r"comments", CommentViewSet, basename="comments")
router.register(r"reports", ReportViewSet, basename="reports")

router.register(r"flashcard-decks", FlashcardDeckViewSet, basename="flashcard-decks")
router.register(r"flashcards", FlashcardViewSet, basename="flashcards")
router.register(r"flashcard-reviews", FlashcardReviewViewSet, basename="flashcard-reviews")

router.register(r"qa-questions", QAQuestionViewSet, basename="qa-questions")
router.register(r"qa-answers", QAAnswerViewSet, basename="qa-answers")

router.register(r"collections", CollectionViewSet, basename="collections")
router.register(r"collection-items", CollectionItemViewSet, basename="collection-items")

urlpatterns = [
    path("", include(router.urls)),
]
