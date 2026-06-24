from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.viewsets import TenantScopedViewSet
from apps.costs.models import CostEntry, ProfitabilityReport
from apps.costs.serializers import (
    CostEntrySerializer,
    ProfitabilityReportSerializer,
)
from apps.costs.services import compute_profitability
from apps.farms.models import Crop
from apps.tenants.models import Role


class CostEntryViewSet(TenantScopedViewSet):
    serializer_class = CostEntrySerializer
    queryset = CostEntry.objects.select_related("crop", "treatment", "operation").all()
    filterset_fields = ["crop", "category", "source"]
    search_fields = ["description"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.get_role() == Role.FARMER:
            qs = qs.filter(crop__parcel__farm__owner=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            cooperative=self.get_cooperative(),
            created_by=self.request.user,
        )


class ProfitabilityReportViewSet(TenantScopedViewSet):
    serializer_class = ProfitabilityReportSerializer
    queryset = ProfitabilityReport.objects.select_related("crop").all()
    filterset_fields = ["crop"]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.get_role() == Role.FARMER:
            qs = qs.filter(crop__parcel__farm__owner=self.request.user)
        return qs

    @action(detail=False, methods=["post"])
    def recompute(self, request):
        """Recompute profitability for one crop (``crop`` id) or all crops."""
        crop_id = request.data.get("crop")
        crops = Crop.objects.filter(cooperative=self.get_cooperative())
        if crop_id:
            crops = crops.filter(id=crop_id)
        reports = [compute_profitability(crop) for crop in crops]
        return Response(self.get_serializer(reports, many=True).data)
