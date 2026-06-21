# apps/academics/serializers.py
from rest_framework import serializers
from .models import Level, Stream, Subject, Chapter, Topic, Tag

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ["id", "name", "order", "is_active"]

class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = ["id", "name", "code", "is_active"]

class SubjectSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source="level.name", read_only=True)
    stream_name = serializers.CharField(source="stream.name", read_only=True)

    class Meta:
        model = Subject
        fields = ["id", "name", "code", "order", "is_active", "level", "level_name", "stream", "stream_name"]

class ChapterSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Chapter
        fields = ["id", "title", "number", "order", "is_active", "subject", "subject_name"]

class TopicSerializer(serializers.ModelSerializer):
    chapter_title = serializers.CharField(source="chapter.title", read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ["id", "title", "order", "is_active", "content", "chapter", "chapter_title", "tags"]

    def get_tags(self, obj):
        return []  # TODO: implement real tags later

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]
