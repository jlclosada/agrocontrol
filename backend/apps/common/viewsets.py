"""Tenant-aware DRF base classes.

Every domain endpoint is scoped to the active cooperative so that data from one
cooperative is never visible to another (prevents cross-tenant IDOR).
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.tenants.permissions import HasCooperativeRole
from apps.tenants.utils import TenantContextMixin


class TenantScopedViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """Filters and assigns the active cooperative automatically.

    Set ``required_roles`` on a subclass to restrict access by role.
    """

    permission_classes = [IsAuthenticated, HasCooperativeRole]

    def get_queryset(self):
        return super().get_queryset().filter(cooperative=self.get_cooperative())

    def perform_create(self, serializer):
        serializer.save(cooperative=self.get_cooperative())
