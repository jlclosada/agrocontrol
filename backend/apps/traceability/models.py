from django.conf import settings
from django.db import models

from apps.common.models import TenantScopedModel


class TraceAction(models.TextChoices):
    CREATE = "CREATE", "Creación"
    UPDATE = "UPDATE", "Modificación"
    DELETE = "DELETE", "Eliminación"


class TraceEvent(TenantScopedModel):
    """An append-only, hash-chained audit event.

    Every domain write produces a ``TraceEvent``. Each event embeds the hash of
    the previous event for its cooperative, forming a tamper-evident chain: any
    retroactive edit breaks every subsequent hash.
    """

    sequence = models.PositiveBigIntegerField(
        help_text="Monotonic position within the cooperative chain."
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trace_events",
    )
    entity_type = models.CharField(max_length=80)
    entity_id = models.UUIDField()
    action = models.CharField(max_length=10, choices=TraceAction.choices)
    payload = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField()
    prev_hash = models.CharField(max_length=64, blank=True)
    hash = models.CharField(max_length=64)

    class Meta(TenantScopedModel.Meta):
        ordering = ["-sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "sequence"],
                name="unique_trace_sequence_per_coop",
            )
        ]
        indexes = [
            models.Index(fields=["cooperative", "entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"#{self.sequence} {self.action} {self.entity_type} {self.entity_id}"
