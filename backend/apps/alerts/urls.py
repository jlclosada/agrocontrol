from rest_framework.routers import DefaultRouter

from apps.alerts.views import AlertRuleViewSet, AlertViewSet

router = DefaultRouter()
router.register("alert-rules", AlertRuleViewSet, basename="alertrule")
router.register("alerts", AlertViewSet, basename="alert")

urlpatterns = router.urls
