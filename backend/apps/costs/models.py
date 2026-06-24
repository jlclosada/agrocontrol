from django.conf import settings
from django.db import models

from apps.common.models import TenantScopedModel


class CostCategory(models.TextChoices):
    LABOR = "LABOR", "Mano de obra"
    PRODUCT = "PRODUCT", "Producto / insumo"
    MACHINE = "MACHINE", "Maquinaria"
    WATER = "WATER", "Agua / riego"
    ELECTRICITY = "ELECTRICITY", "Electricidad"
    OTHER = "OTHER", "Otro"


class CostSource(models.TextChoices):
    MANUAL = "MANUAL", "Manual"
    TREATMENT = "TREATMENT", "Tratamiento"
    OPERATION = "OPERATION", "Operación de campo"


class CostEntry(TenantScopedModel):
    """A cost imputed to a crop. May be created manually or auto-derived.

    Auto-derived entries link back to their origin (treatment/operation) so they
    are idempotent: re-running imputation never duplicates a cost.
    """

    crop = models.ForeignKey(
        "farms.Crop", on_delete=models.CASCADE, related_name="cost_entries"
    )
    category = models.CharField(max_length=20, choices=CostCategory.choices)
    source = models.CharField(
        max_length=20, choices=CostSource.choices, default=CostSource.MANUAL
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)

    treatment = models.ForeignKey(
        "fieldbook.Treatment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cost_entries",
    )
    operation = models.ForeignKey(
        "fieldbook.FieldOperation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cost_entries",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cost_entries",
    )

    class Meta(TenantScopedModel.Meta):
        ordering = ["-date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["treatment"],
                condition=models.Q(treatment__isnull=False),
                name="unique_cost_per_treatment",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_category_display()} {self.amount} — {self.crop}"


class ProfitabilityReport(TenantScopedModel):
    """A snapshot of a crop's economics: cost, income and margin."""

    crop = models.OneToOneField(
        "farms.Crop", on_delete=models.CASCADE, related_name="profitability"
    )
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    income = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    cost_per_ha = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    margin_pct = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    computed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Rentabilidad {self.crop}: {self.profit}"
