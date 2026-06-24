from apps.common.viewsets import TenantScopedViewSet
from apps.fieldbook.models import FieldOperation, Treatment
from apps.fieldbook.serializers import FieldOperationSerializer, TreatmentSerializer
from apps.tenants.models import Role


class FieldOperationViewSet(TenantScopedViewSet):
    serializer_class = FieldOperationSerializer
    queryset = FieldOperation.objects.select_related("crop").all()
    filterset_fields = ["crop", "operation_type", "date"]
    search_fields = ["description"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.get_role() == Role.FARMER:
            qs = qs.filter(crop__parcel__farm__owner=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            cooperative=self.get_cooperative(),
            performed_by=self.request.user,
        )


class TreatmentViewSet(TenantScopedViewSet):
    serializer_class = TreatmentSerializer
    queryset = Treatment.objects.select_related("crop", "product").all()
    filterset_fields = ["crop", "product", "date"]
    search_fields = ["target_pest"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.get_role() == Role.FARMER:
            qs = qs.filter(crop__parcel__farm__owner=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            cooperative=self.get_cooperative(),
            applicator=self.request.user,
        )
