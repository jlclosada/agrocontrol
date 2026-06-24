from django.db import models

from apps.common.models import TenantScopedModel


class AlertTrigger(models.TextChoices):
    STOCK = "STOCK", "Stock mínimo"
    EXPIRY = "EXPIRY", "Caducidad de lote"
    SAFETY = "SAFETY", "Plazo de seguridad"
    COMPLIANCE = "COMPLIANCE", "Cumplimiento normativo"
    WEATHER = "WEATHER", "Meteorología"
    PRODUCTION = "PRODUCTION", "Producción"
    MAINTENANCE = "MAINTENANCE", "Mantenimiento"


class AlertSeverity(models.TextChoices):
    INFO = "INFO", "Información"
    LOW = "LOW", "Baja"
    MEDIUM = "MEDIUM", "Media"
    HIGH = "HIGH", "Alta"
    CRITICAL = "CRITICAL", "Crítica"


class AlertRule(TenantScopedModel):
    """A configurable rule that produces alerts when its condition holds.

    ``condition`` is a JSON object interpreted by the evaluator for each trigger
    (e.g. ``{"days": 30}`` for EXPIRY). Rules are evaluated periodically by a
    Celery beat task and may also be triggered on demand.
    """

    name = models.CharField(max_length=200)
    trigger = models.CharField(max_length=20, choices=AlertTrigger.choices)
    condition = models.JSONField(default=dict, blank=True)
    severity = models.CharField(
        max_length=10, choices=AlertSeverity.choices, default=AlertSeverity.MEDIUM
    )
    is_active = models.BooleanField(default=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["trigger", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_trigger_display()})"


class Alert(TenantScopedModel):
    """An alert instance raised by a rule.

    ``dedupe_key`` keeps periodic evaluation idempotent: an open alert with the
    same key is updated rather than duplicated.
    """

    rule = models.ForeignKey(
        AlertRule, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="alerts",
    )
    trigger = models.CharField(max_length=20, choices=AlertTrigger.choices)
    severity = models.CharField(
        max_length=10, choices=AlertSeverity.choices, default=AlertSeverity.MEDIUM
    )
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True)
    dedupe_key = models.CharField(max_length=200, db_index=True)
    acknowledged = models.BooleanField(default=False)
    resolved = models.BooleanField(default=False)

    class Meta(TenantScopedModel.Meta):
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "dedupe_key"],
                condition=models.Q(resolved=False),
                name="unique_open_alert_per_key",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.severity}] {self.title}"
