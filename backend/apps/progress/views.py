from django.utils import timezone
from django.db.models import Sum, Count, Avg

from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import TopicProgress, DailyActivity, StudyStreak, UserGoal
from .serializers import (
    TopicProgressSerializer, DailyActivitySerializer, StudyStreakSerializer,
    WeakTopicSerializer, DueTopicSerializer, UserGoalSerializer, SnapshotSerializer,
    DashboardSerializer
)
from .selectors import get_due_topics, get_activity_range, get_weak_topics, get_snapshots
from .recommendations import build_recommendations




class TopicProgressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TopicProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TopicProgress.objects.filter(user=self.request.user).select_related("topic")
        chapter_id = self.request.query_params.get("chapter_id")
        if chapter_id:
            qs = qs.filter(topic__chapter_id=chapter_id)
        return qs.order_by("-updated_at")
    


    @action(detail=False, methods=["get"], url_path="recommendations")
    def recommendations(self, request):
        limit = int(request.query_params.get("limit", 10))
        data = build_recommendations(request.user, limit=limit)
        return Response({"results": data})



class DailyActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DailyActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = DailyActivity.objects.filter(user=self.request.user).order_by("-date")
        f = self.request.query_params.get("from")
        t = self.request.query_params.get("to")
        if f:
            qs = qs.filter(date__gte=f)
        if t:
            qs = qs.filter(date__lte=t)
        return qs


class GoalViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj, _ = UserGoal.objects.get_or_create(user=self.request.user)
        return obj

    def list(self, request, *args, **kwargs):
        obj, _ = UserGoal.objects.get_or_create(user=request.user)
        return Response(self.get_serializer(obj).data)


class SnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SnapshotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        f = self.request.query_params.get("from")
        t = self.request.query_params.get("to")
        return get_snapshots(user, from_date=f, to_date=t)


class ProgressViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        user = request.user
        today = timezone.localdate()

        today_obj = DailyActivity.objects.filter(user=user, date=today).first() or DailyActivity(user=user, date=today)
        streak_obj = StudyStreak.objects.filter(user=user).first() or StudyStreak(user=user)
        goal_obj, _ = UserGoal.objects.get_or_create(user=user)

        totals = TopicProgress.objects.filter(user=user).aggregate(
            topics=Count("id"),
            total_answered=Sum("total_answered"),
            correct=Sum("correct"),
            avg_mastery=Avg("mastery"),
        )
        totals = {k: (float(v) if isinstance(v, float) else int(v or 0)) for k, v in totals.items()}

        qs = TopicProgress.objects.filter(user=user)
        mastery_buckets = {
            "0_25": qs.filter(mastery__lt=25).count(),
            "26_50": qs.filter(mastery__gte=25, mastery__lt=50).count(),
            "51_75": qs.filter(mastery__gte=50, mastery__lt=75).count(),
            "76_100": qs.filter(mastery__gte=75).count(),
        }

        weak = get_weak_topics(user, limit=10)
        due = get_due_topics(user, limit=10)
        activity_7d = get_activity_range(user, days=7)

        payload = {
            "today": DailyActivitySerializer(today_obj).data,
            "streak": StudyStreakSerializer(streak_obj).data,
            "goals": UserGoalSerializer(goal_obj).data,
            "totals": totals,
            "mastery_buckets": mastery_buckets,
            "weak_topics": WeakTopicSerializer(weak, many=True).data,
            "due_topics": DueTopicSerializer(due, many=True).data,
            "activity_7d": DailyActivitySerializer(activity_7d, many=True).data,
        }
        return Response(DashboardSerializer(payload).data)

    @action(detail=False, methods=["get"], url_path="due-topics")
    def due_topics(self, request):
        limit = int(request.query_params.get("limit", 20))
        qs = get_due_topics(request.user, limit=limit)
        return Response(DueTopicSerializer(qs, many=True).data)
