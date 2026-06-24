"""Resolves the active cooperative for each authenticated request.

The client selects a tenant by sending the ``X-Cooperative`` header with the
cooperative slug or id. If omitted, the user's first active membership is used.
"""
from apps.tenants.models import CooperativeMembership


class CooperativeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.cooperative = None
        request.membership = None
        request.role = None
        self._resolve(request)
        return self.get_response(request)

    @staticmethod
    def _resolve(request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return

        requested = request.headers.get("X-Cooperative")
        qs = CooperativeMembership.objects.select_related("cooperative").filter(
            user=user, is_active=True, cooperative__is_active=True
        )
        membership = None
        if requested:
            membership = qs.filter(
                cooperative__slug=requested
            ).first() or qs.filter(cooperative__id=requested).first()
        else:
            membership = qs.first()

        if membership:
            request.membership = membership
            request.cooperative = membership.cooperative
            request.role = membership.role
