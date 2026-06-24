from django.contrib import admin

from apps.inventory.models import Product, StockBatch, StockMovement


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "unit", "reorder_level", "cooperative"]
    list_filter = ["cooperative", "category"]
    search_fields = ["name", "active_ingredient", "registration_number"]


@admin.register(StockBatch)
class StockBatchAdmin(admin.ModelAdmin):
    list_display = ["product", "lot", "expiry_date", "received_date", "cooperative"]
    list_filter = ["cooperative", "expiry_date"]
    search_fields = ["lot", "product__name"]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["product", "batch", "movement_type", "quantity", "created_at"]
    list_filter = ["cooperative", "movement_type"]
    search_fields = ["product__name", "reason"]
