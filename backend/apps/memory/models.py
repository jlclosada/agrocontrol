from django.conf import settings
from django.db import models

from apps.common.models import TenantScopedModel


class MemoryScope(models.TextChoices):
    USER = "USER", "Memoria de usuario"
    PARCEL = "PARCEL", "Memoria de parcela/cultivo"
    GLOBAL = "GLOBAL", "Memoria global del sistema"


class MemoryEntry(TenantScopedModel):
    """A single persistent memory item, consultable by AI agents.

    Three levels are supported via ``scope``:
      - USER:   tied to a ``user`` (preferences, history).
      - PARCEL: tied to a ``parcel`` and/or ``crop`` (state, incidents, soil).
      - GLOBAL: cooperative-wide trends and aggregated learnings.
    """

    scope = models.CharField(max_length=10, choices=MemoryScope.choices)

    # Optional links depending on scope (kept nullable for flexibility).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="memories",
    )
    parcel = models.ForeignKey(
        "farms.Parcel",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="memories",
    )
    crop = models.ForeignKey(
        "farms.Crop",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="memories",
    )

    key = models.CharField(max_length=120, blank=True, help_text="Optional dedup key.")
    content = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    importance = models.PositiveSmallIntegerField(default=1)
    source = models.CharField(
        max_length=60, default="system",
        help_text="Who wrote it: 'system', 'agent:<name>', 'user'.",
    )
    # Reserved for semantic search (pgvector). Stored as list for portability now.
    embedding = models.JSONField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["-importance", "-created_at"]
        indexes = [
            models.Index(fields=["cooperative", "scope"]),
            models.Index(fields=["cooperative", "scope", "key"]),
        ]

    def __str__(self) -> str:
        return f"[{self.scope}] {self.content[:60]}"
