from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.viewsets import TenantScopedViewSet
from apps.inventory.models import Product, StockBatch, StockMovement
from apps.inventory.serializers import (
    ProductSerializer,
    StockBatchSerializer,
    StockMovementSerializer,
)


class ProductViewSet(TenantScopedViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    filterset_fields = ["category"]
    search_fields = ["name", "active_ingredient", "registration_number"]

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        products = [p for p in self.get_queryset() if p.needs_reorder]
        return Response(self.get_serializer(products, many=True).data)


class StockBatchViewSet(TenantScopedViewSet):
    serializer_class = StockBatchSerializer
    queryset = StockBatch.objects.select_related("product").all()
    filterset_fields = ["product", "lot"]
    search_fields = ["lot", "product__name"]

    @action(detail=False, methods=["get"])
    def expiring(self, request):
        """Batches already expired or expiring within ``days`` (default 30)."""
        from datetime import timedelta

        from django.utils import timezone

        try:
            days = int(request.query_params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
        limit = timezone.localdate() + timedelta(days=days)
        batches = [
            b for b in self.get_queryset()
            if b.expiry_date and b.expiry_date <= limit and b.quantity > 0
        ]
        return Response(self.get_serializer(batches, many=True).data)


class StockMovementViewSet(TenantScopedViewSet):
    serializer_class = StockMovementSerializer
    queryset = StockMovement.objects.select_related("product", "batch").all()
    filterset_fields = ["product", "movement_type", "batch"]
