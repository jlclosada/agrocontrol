"""Audit logging helpers."""


def record_audit(event, request=None, user=None, email="", cooperative=None, detail=""):
    """Persist an :class:`AuditLog` entry, capturing request metadata."""
    from apps.audit.models import AuditLog

    ip = None
    user_agent = ""
    if request is not None:
        ip = _client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:400]

    return AuditLog.objects.create(
        event=event,
        user=user if (user and getattr(user, "pk", None)) else None,
        email=email or (getattr(user, "email", "") if user else ""),
        cooperative=cooperative,
        ip_address=ip,
        user_agent=user_agent,
        detail=detail[:255],
    )


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
