import uuid

from django.conf import settings
from django.db import models


class AuditEvent(models.TextChoices):
    LOGIN_SUCCESS = "LOGIN_SUCCESS", "Inicio de sesión correcto"
    LOGIN_FAILED = "LOGIN_FAILED", "Inicio de sesión fallido"
    LOGIN_MFA_REQUIRED = "LOGIN_MFA_REQUIRED", "MFA requerido"
    MFA_ENROLLED = "MFA_ENROLLED", "MFA registrado"
    LOGOUT = "LOGOUT", "Cierre de sesión"
    USER_REGISTERED = "USER_REGISTERED", "Alta de usuario"
    PASSWORD_CHANGED = "PASSWORD_CHANGED", "Cambio de contraseña"
    MEMBER_ADDED = "MEMBER_ADDED", "Miembro añadido al equipo"
    MEMBER_ROLE_CHANGED = "MEMBER_ROLE_CHANGED", "Cambio de rol de miembro"
    MEMBER_DEACTIVATED = "MEMBER_DEACTIVATED", "Miembro desactivado"
    MEMBER_REACTIVATED = "MEMBER_REACTIVATED", "Miembro reactivado"
    MEMBER_ACCOUNT_CREATED = "MEMBER_ACCOUNT_CREATED", "Cuenta de acceso creada"


class AuditLog(models.Model):
    """An immutable record of an authentication/security event.

    Not tenant-scoped: a failed login may not resolve to a cooperative, and the
    same user can act across tenants. ``cooperative`` is captured when known.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.CharField(max_length=32, choices=AuditEvent.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    email = models.EmailField(blank=True, help_text="Captured even if user is unknown.")
    cooperative = models.ForeignKey(
        "tenants.Cooperative",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=400, blank=True)
    detail = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event", "created_at"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return f"{self.event} {self.email} @ {self.created_at:%Y-%m-%d %H:%M}"
