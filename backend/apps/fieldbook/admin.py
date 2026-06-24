from django.contrib import admin

from apps.fieldbook.models import FieldOperation, Treatment


@admin.register(FieldOperation)
class FieldOperationAdmin(admin.ModelAdmin):
    list_display = ["operation_type", "crop", "date", "performed_by", "cooperative"]
    list_filter = ["cooperative", "operation_type", "date"]
    search_fields = ["description"]


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ["product", "crop", "date", "dose", "total_quantity"]
    list_filter = ["cooperative", "date"]
    search_fields = ["target_pest", "product__name"]
