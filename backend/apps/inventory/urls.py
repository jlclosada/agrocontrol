from rest_framework.routers import DefaultRouter

from apps.inventory.views import (
    ProductViewSet,
    StockBatchViewSet,
    StockMovementViewSet,
)

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("stock-batches", StockBatchViewSet, basename="stockbatch")
router.register("stock-movements", StockMovementViewSet, basename="stockmovement")

urlpatterns = router.urls
