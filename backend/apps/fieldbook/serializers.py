from rest_framework import serializers

from apps.fieldbook.models import FieldOperation, Treatment


class FieldOperationSerializer(serializers.ModelSerializer):
    operation_type_display = serializers.CharField(
        source="get_operation_type_display", read_only=True
    )

    class Meta:
        model = FieldOperation
        fields = [
            "id", "crop", "operation_type", "operation_type_display", "date",
            "description", "area_ha", "performed_by", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TreatmentSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    crop_label = serializers.CharField(source="crop.__str__", read_only=True)

    class Meta:
        model = Treatment
        fields = [
            "id", "operation", "crop", "crop_label", "product", "product_name",
            "date", "dose", "dose_unit", "total_quantity", "target_pest",
            "weather", "applicator", "safety_interval_ok", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
