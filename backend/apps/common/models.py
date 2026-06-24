import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base with UUID pk and created/updated timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class TenantScopedModel(TimeStampedModel):
    """Abstract base for every model that belongs to a cooperative (tenant)."""

    cooperative = models.ForeignKey(
        "tenants.Cooperative",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
