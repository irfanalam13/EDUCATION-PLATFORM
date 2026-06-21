from django.utils.text import Truncator
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AIDocument, AIChatSession
from .serializers import (
    AIDocumentSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatSessionListSerializer,
    ChatSessionSerializer,
)
from .services import answer_learning_question, process_document


class AIDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = AIDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "extracted_text"]
    ordering_fields = ["created_at", "updated_at", "status", "size"]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return (
            AIDocument.objects.filter(user=self.request.user)
            .prefetch_related("chunks")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        upload = self.request.FILES.get("file")
        fallback_title = getattr(upload, "name", "Learning document") if upload else "Learning document"
        title = serializer.validated_data.get("title") or Truncator(fallback_title).chars(240)
        mime_type = getattr(upload, "content_type", "") if upload else ""
        document = serializer.save(user=self.request.user, title=title, mime_type=mime_type)
        process_document(document)

    @action(detail=True, methods=["post"], url_path="reprocess")
    def reprocess(self, request, pk=None):
        document = self.get_object()
        process_document(document)
        return Response(self.get_serializer(document).data, status=status.HTTP_200_OK)


class AIChatSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "messages__content"]
    ordering_fields = ["created_at", "updated_at", "title"]
    http_method_names = ["get", "delete", "head", "options"]

    def get_queryset(self):
        return (
            AIChatSession.objects.filter(user=self.request.user)
            .prefetch_related("messages")
            .order_by("-updated_at")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ChatSessionListSerializer
        return ChatSessionSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    serializer = ChatRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    payload = answer_learning_question(
        user=request.user,
        message=serializer.validated_data["message"],
        session_id=serializer.validated_data.get("session_id"),
    )
    return Response(ChatResponseSerializer(payload).data)
