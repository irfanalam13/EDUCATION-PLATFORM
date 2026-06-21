from rest_framework.routers import DefaultRouter
from .views import (
    LevelViewSet,
    StreamViewSet,
    SubjectViewSet,
    ChapterViewSet,
    TopicViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register(r"levels", LevelViewSet, basename="levels")
router.register(r"streams", StreamViewSet, basename="streams")
router.register(r"subjects", SubjectViewSet, basename="subjects")
router.register(r"chapters", ChapterViewSet, basename="chapters")
router.register(r"topics", TopicViewSet, basename="topics")
router.register(r"tags", TagViewSet, basename="tags")

urlpatterns = router.urls
