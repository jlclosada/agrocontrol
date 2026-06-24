from rest_framework.permissions import SAFE_METHODS, BasePermission


def _membership(request, view):
    """Get the resolved membership, preferring the view's cached context."""
    if hasattr(view, "get_membership"):
        return view.get_membership()
    return getattr(request, "membership", None)


class IsCooperativeMember(BasePermission):
    message = "You must belong to an active cooperative."

    def has_permission(self, request, view):
        return bool(_membership(request, view))


class HasCooperativeRole(BasePermission):
    """Active membership required; optionally restricted by ``view.required_roles``.

    Read-only roles (AUDITOR) are denied any unsafe (write) method, and write
    roles are required for unsafe methods even when ``required_roles`` is unset.
    """

    message = "Your role does not allow this action."

    def has_permission(self, request, view):
        from apps.tenants.models import READONLY_ROLES, WRITE_ROLES

        membership = _membership(request, view)
        if membership is None:
            return False

        if request.method not in SAFE_METHODS:
            if membership.role in READONLY_ROLES:
                return False
            if membership.role not in WRITE_ROLES:
                return False

        required = getattr(view, "required_roles", None)
        if not required:
            return True
        return membership.role in required


class IsCoopAdmin(BasePermission):
    def has_permission(self, request, view):
        from apps.tenants.models import ADMIN_ROLES

        membership = _membership(request, view)
        return bool(membership) and membership.role in ADMIN_ROLES
