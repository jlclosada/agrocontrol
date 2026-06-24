"""Helpers to resolve the active cooperative for a request.

DRF authenticates (JWT) at the view layer, so the reliable place to resolve the
tenant is inside the view using ``request.user``. This module is the single
source of truth used by both ViewSets and plain APIViews.
"""
from apps.tenants.models import CooperativeMembership


def resolve_membership(user, requested=None):
    if not user or not user.is_authenticated:
        return None

    qs = CooperativeMembership.objects.select_related("cooperative").filter(
        user=user, is_active=True, cooperative__is_active=True
    )
    if requested:
        return (
            qs.filter(cooperative__slug=requested).first()
            or qs.filter(cooperative__id=requested).first()
        )
    return qs.first()


class TenantContextMixin:
    """Resolves and caches ``cooperative``/``role`` for the current request."""

    def get_membership(self):
        if getattr(self, "_membership", None) is None:
            requested = self.request.headers.get("X-Cooperative")
            self._membership = resolve_membership(self.request.user, requested)
        return self._membership

    def get_cooperative(self):
        from rest_framework.exceptions import PermissionDenied

        membership = self.get_membership()
        if membership is None:
            raise PermissionDenied("No active cooperative for this request.")
        return membership.cooperative

    def get_role(self):
        membership = self.get_membership()
        return membership.role if membership else None
