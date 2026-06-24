from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from apps.accounts.views import AuditTokenObtainPairView

api_v1 = [
    path("auth/token/", AuditTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include("apps.accounts.urls")),
    path("", include("apps.tenants.urls")),
    path("", include("apps.farms.urls")),
    path("", include("apps.fieldbook.urls")),
    path("", include("apps.inventory.urls")),
    path("", include("apps.memory.urls")),
    path("", include("apps.agents.urls")),
    path("", include("apps.traceability.urls")),
    path("", include("apps.costs.urls")),
    path("", include("apps.alerts.urls")),
    path("", include("apps.analytics.urls")),
    path("", include("apps.audit.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1, "api"), namespace="v1")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
