# apps/academics/views.py
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny

from .models import Level, Stream, Subject, Chapter, Topic, Tag
from .serializers import (
    LevelSerializer, StreamSerializer, SubjectSerializer,
    ChapterSerializer, TopicSerializer, TagSerializer
)

# The curriculum catalogue is intentionally public (anonymous browsing on the
# marketing/academics pages). Every other API defaults to IsAuthenticated.

class LevelViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Level.objects.all().order_by("id")
    serializer_class = LevelSerializer

class StreamViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Stream.objects.all().order_by("id")
    serializer_class = StreamSerializer

class SubjectViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = SubjectSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]

    def get_queryset(self):
        qs = Subject.objects.select_related("level", "stream").all()
        level = self.request.query_params.get("level")
        stream = self.request.query_params.get("stream")

        if level:
            qs = qs.filter(level_id=level)
        if stream:
            qs = qs.filter(stream_id=stream)

        return qs.order_by("id")

class ChapterViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ChapterSerializer

    def get_queryset(self):
        qs = Chapter.objects.select_related("subject").all()
        subject = self.request.query_params.get("subject")

        if subject:
            qs = qs.filter(subject_id=subject)

        return qs.order_by("id")

class TopicViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = TopicSerializer

    def get_queryset(self):
        qs = Topic.objects.select_related("chapter").all()
        chapter = self.request.query_params.get("chapter")

        if chapter:
            qs = qs.filter(chapter_id=chapter)

        return qs.order_by("id")

class TagViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    queryset = Tag.objects.all().order_by("id")
    serializer_class = TagSerializer
