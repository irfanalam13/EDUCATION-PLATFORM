from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import include, path

from apps.accounts.views import CookieTokenRefreshView, DevTokenObtainPairView

# urls.py (Main Project URLs)

from drf_spectacular.views import (
    SpectacularAPIView, 
    SpectacularRedocView, 
    SpectacularSwaggerView
)

def home(request):
    return JsonResponse(
        {
            "status": "ok",
            "message": "Edu Platform API is running",
        }
    )


def healthz(request):
    """Liveness probe for Docker/orchestrators (no auth, no host coupling)."""
    return JsonResponse({"status": "ok"})


def favicon(request):
    """Browsers auto-request /favicon.ico; this API has no icon. Return an empty
    204 so it doesn't render a noisy debug-404 page in dev."""
    return HttpResponse(status=204)


urlpatterns = [
    path("", home),
    path("healthz/", healthz),
    path("favicon.ico", favicon),
    path("admin/", admin.site.urls),

    # 2. Schema download (Generates the schema YAML/JSON file)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # 3. Swagger UI (The visual interactive documentation page)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # 4. Redoc UI (An alternative, cleaner three-column documentation view)
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path("api/auth/token/", DevTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("api/accounts/", include("apps.accounts.urls")),
    path("api/ai/", include("apps.ai.urls")),
    path("api/ai/", include("apps.ai_learning.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/academics/", include("apps.academics.urls")),
    path("api/content/", include("apps.content.urls")),
    path("api/gamification/", include("apps.gamification.urls")),
    path("api/assessment/", include("apps.assessment.urls")),
    path("api/progress/", include("apps.progress.urls")),
    path("api/institutions/", include("apps.institutions.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/moderation/", include("apps.moderation.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
