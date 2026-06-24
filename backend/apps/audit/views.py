from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.tenants.models import ADMIN_ROLES, AUDITOR_ROLE_SET
from apps.tenants.permissions import HasCooperativeRole
from apps.tenants.utils import TenantContextMixin


class AuditLogViewSet(
    TenantContextMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """Read-only access to the audit trail for admins and auditors.

    Scoped to the active cooperative plus the requesting user's own events.
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasCooperativeRole]
    required_roles = ADMIN_ROLES | AUDITOR_ROLE_SET
    filterset_fields = ["event", "user"]
    search_fields = ["email", "detail", "ip_address"]

    def get_queryset(self):
        cooperative = self.get_cooperative()
        from django.db.models import Q

        return AuditLog.objects.filter(
            Q(cooperative=cooperative) | Q(user=self.request.user)
        ).select_related("user", "cooperative")
