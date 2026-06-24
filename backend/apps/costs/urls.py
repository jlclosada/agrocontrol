from rest_framework.routers import DefaultRouter

from apps.costs.views import CostEntryViewSet, ProfitabilityReportViewSet

router = DefaultRouter()
router.register("cost-entries", CostEntryViewSet, basename="costentry")
router.register(
    "profitability", ProfitabilityReportViewSet, basename="profitability"
)

urlpatterns = router.urls
