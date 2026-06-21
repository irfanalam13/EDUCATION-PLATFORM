from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, DeviceViewSet

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"devices", DeviceViewSet, basename="devices")

urlpatterns = router.urls
