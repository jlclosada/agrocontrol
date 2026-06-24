from rest_framework import serializers

from apps.inventory.models import Product, StockBatch, StockMovement


class ProductSerializer(serializers.ModelSerializer):
    current_stock = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    needs_reorder = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "registration_number", "active_ingredient", "category",
            "unit", "safety_interval_days", "reorder_level", "unit_cost",
            "current_stock", "needs_reorder", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class StockBatchSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockBatch
        fields = [
            "id", "product", "product_name", "lot", "expiry_date",
            "received_date", "quantity", "is_expired", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "product", "product_name", "batch", "movement_type", "quantity",
            "signed_quantity", "reason", "treatment", "created_at",
        ]
        read_only_fields = ["id", "signed_quantity", "created_at"]
