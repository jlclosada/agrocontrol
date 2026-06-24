from rest_framework.decorators import action
from rest_framework.response import Response

from apps.alerts.models import Alert, AlertRule
from apps.alerts.serializers import AlertRuleSerializer, AlertSerializer
from apps.alerts.services import evaluate_cooperative
from apps.common.viewsets import TenantScopedViewSet


class AlertRuleViewSet(TenantScopedViewSet):
    serializer_class = AlertRuleSerializer
    queryset = AlertRule.objects.all()
    filterset_fields = ["trigger", "severity", "is_active"]
    search_fields = ["name"]

    @action(detail=False, methods=["post"])
    def evaluate(self, request):
        """Evaluate all active rules now and return the open alerts raised."""
        alerts = evaluate_cooperative(self.get_cooperative())
        return Response(AlertSerializer(alerts, many=True).data)


class AlertViewSet(TenantScopedViewSet):
    serializer_class = AlertSerializer
    queryset = Alert.objects.select_related("rule").all()
    filterset_fields = ["trigger", "severity", "acknowledged", "resolved"]
    search_fields = ["title", "message"]
    http_method_names = ["get", "patch", "head", "options"]

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        alert.acknowledged = True
        alert.save(update_fields=["acknowledged", "updated_at"])
        return Response(self.get_serializer(alert).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.resolved = True
        alert.acknowledged = True
        alert.save(update_fields=["resolved", "acknowledged", "updated_at"])
        return Response(self.get_serializer(alert).data)
