from django.conf import settings
from django.db import models

from apps.common.models import TenantScopedModel


class OperationType(models.TextChoices):
    SOWING = "SOWING", "Siembra"
    FERTILIZATION = "FERTILIZATION", "Abonado"
    IRRIGATION = "IRRIGATION", "Riego"
    TREATMENT = "TREATMENT", "Tratamiento fitosanitario"
    PRUNING = "PRUNING", "Poda"
    HARVEST = "HARVEST", "Cosecha"
    OTHER = "OTHER", "Otro"


class FieldOperation(TenantScopedModel):
    """A digital field-notebook entry. Legally required in many EU countries."""

    crop = models.ForeignKey(
        "farms.Crop", on_delete=models.CASCADE, related_name="operations"
    )
    operation_type = models.CharField(max_length=20, choices=OperationType.choices)
    date = models.DateField()
    description = models.TextField(blank=True)
    area_ha = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="field_operations",
    )

    class Meta(TenantScopedModel.Meta):
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.get_operation_type_display()} — {self.crop} ({self.date})"


class Treatment(TenantScopedModel):
    """A phytosanitary treatment. Drives stock consumption and traceability."""

    operation = models.OneToOneField(
        FieldOperation,
        on_delete=models.CASCADE,
        related_name="treatment",
        null=True,
        blank=True,
    )
    crop = models.ForeignKey(
        "farms.Crop", on_delete=models.CASCADE, related_name="treatments"
    )
    product = models.ForeignKey(
        "inventory.Product", on_delete=models.PROTECT, related_name="treatments"
    )
    date = models.DateField()
    dose = models.DecimalField(max_digits=12, decimal_places=4)
    dose_unit = models.CharField(max_length=20, default="L/ha")
    total_quantity = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Total product consumed (in product unit).",
    )
    target_pest = models.CharField(max_length=200, blank=True)
    weather = models.CharField(max_length=200, blank=True)
    applicator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="treatments",
    )
    safety_interval_ok = models.BooleanField(default=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.product} on {self.crop} ({self.date})"

    @property
    def earliest_safe_harvest_date(self):
        """Date from which harvest is allowed given the pre-harvest interval."""
        from datetime import timedelta

        days = self.product.safety_interval_days if self.product_id else 0
        if not self.date:
            return None
        return self.date + timedelta(days=days)

    def compute_safety_interval_ok(self) -> bool:
        """A treatment is safe if the crop's harvest is not earlier than the PHI."""
        safe_from = self.earliest_safe_harvest_date
        harvest = getattr(self.crop, "expected_harvest_date", None)
        if safe_from is None or harvest is None:
            return True
        return harvest >= safe_from

    def save(self, *args, **kwargs):
        self.safety_interval_ok = self.compute_safety_interval_ok()
        super().save(*args, **kwargs)
