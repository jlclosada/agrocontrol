from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tenants.permissions import HasCooperativeRole
from apps.tenants.utils import TenantContextMixin
from apps.traceability.models import TraceEvent
from apps.traceability.serializers import TraceEventSerializer
from apps.traceability.services import verify_chain


class TraceEventViewSet(TenantContextMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only access to the append-only traceability chain.

    Events are immutable by design, so only list/retrieve and a ``verify``
    action are exposed.
    """

    serializer_class = TraceEventSerializer
    permission_classes = [IsAuthenticated, HasCooperativeRole]
    queryset = TraceEvent.objects.select_related("actor").all()
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["entity_type", "entity_id", "action", "actor"]
    ordering_fields = ["sequence", "occurred_at"]

    def get_queryset(self):
        return super().get_queryset().filter(cooperative=self.get_cooperative())

    @action(detail=False, methods=["get"])
    def verify(self, request):
        """Recompute the hash chain and report its integrity."""
        return Response(verify_chain(self.get_cooperative()))
