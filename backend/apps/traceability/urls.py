from rest_framework.routers import DefaultRouter

from apps.traceability.views import TraceEventViewSet

router = DefaultRouter()
router.register("trace-events", TraceEventViewSet, basename="trace-event")

urlpatterns = router.urls
