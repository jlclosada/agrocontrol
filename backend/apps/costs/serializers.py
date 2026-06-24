from rest_framework import serializers

from apps.costs.models import CostEntry, ProfitabilityReport


class CostEntrySerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    crop_label = serializers.CharField(source="crop.__str__", read_only=True)

    class Meta:
        model = CostEntry
        fields = [
            "id", "crop", "crop_label", "category", "category_display", "source",
            "amount", "date", "description", "treatment", "operation",
            "created_by", "created_at",
        ]
        read_only_fields = ["id", "source", "created_at"]


class ProfitabilityReportSerializer(serializers.ModelSerializer):
    crop_label = serializers.CharField(source="crop.__str__", read_only=True)

    class Meta:
        model = ProfitabilityReport
        fields = [
            "id", "crop", "crop_label", "total_cost", "income", "profit",
            "cost_per_ha", "margin_pct", "computed_at",
        ]
        read_only_fields = fields
