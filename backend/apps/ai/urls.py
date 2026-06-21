from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AIDocumentViewSet, AIChatSessionViewSet, chat


router = DefaultRouter()
router.register("documents", AIDocumentViewSet, basename="ai-documents")
router.register("sessions", AIChatSessionViewSet, basename="ai-sessions")


urlpatterns = [
    path("", include(router.urls)),
    path("chat/", chat, name="ai-chat"),
]
