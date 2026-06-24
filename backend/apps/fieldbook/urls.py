from rest_framework.routers import DefaultRouter

from apps.fieldbook.views import FieldOperationViewSet, TreatmentViewSet

router = DefaultRouter()
router.register("operations", FieldOperationViewSet, basename="operation")
router.register("treatments", TreatmentViewSet, basename="treatment")

urlpatterns = router.urls
