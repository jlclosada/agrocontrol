from decimal import Decimal

from django.db import models
from django.db.models import Sum

from apps.common.models import TenantScopedModel


class ProductCategory(models.TextChoices):
    HERBICIDE = "HERBICIDE", "Herbicida"
    FUNGICIDE = "FUNGICIDE", "Fungicida"
    INSECTICIDE = "INSECTICIDE", "Insecticida"
    FERTILIZER = "FERTILIZER", "Fertilizante"
    OTHER = "OTHER", "Otro"


class Product(TenantScopedModel):
    """A phytosanitary product / input held in cooperative or farm stock."""

    name = models.CharField(max_length=200)
    registration_number = models.CharField(
        "nº registro", max_length=60, blank=True,
        help_text="Official phytosanitary registration number.",
    )
    active_ingredient = models.CharField(max_length=200, blank=True)
    category = models.CharField(
        max_length=20, choices=ProductCategory.choices, default=ProductCategory.OTHER
    )
    unit = models.CharField(max_length=20, default="L", help_text="L, kg, units…")
    safety_interval_days = models.PositiveIntegerField(
        default=0, help_text="Plazo de seguridad (pre-harvest interval)."
    )
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(
        max_digits=12, decimal_places=4, default=0,
        help_text="Cost per unit, used for automatic cost imputation.",
    )

    class Meta(TenantScopedModel.Meta):
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    @property
    def current_stock(self) -> Decimal:
        agg = self.movements.aggregate(total=Sum("signed_quantity"))
        return agg["total"] or Decimal("0")

    @property
    def needs_reorder(self) -> bool:
        return self.current_stock <= self.reorder_level


class StockBatch(TenantScopedModel):
    """A received lot of a product with its own expiry date (FEFO unit).

    Available quantity is the signed sum of movements linked to this batch.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="batches"
    )
    lot = models.CharField(max_length=80, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["expiry_date", "created_at"]

    def __str__(self) -> str:
        suffix = f" (cad. {self.expiry_date})" if self.expiry_date else ""
        return f"{self.product.name} · lote {self.lot or '—'}{suffix}"

    @property
    def quantity(self) -> Decimal:
        agg = self.movements.aggregate(total=Sum("signed_quantity"))
        return agg["total"] or Decimal("0")

    @property
    def is_expired(self) -> bool:
        from django.utils import timezone

        return bool(self.expiry_date and self.expiry_date < timezone.localdate())


class MovementType(models.TextChoices):
    IN = "IN", "Entrada"
    OUT = "OUT", "Salida"
    ADJUST = "ADJUST", "Ajuste"


class StockMovement(TenantScopedModel):
    """An immutable stock ledger entry. Balance is the sum of signed quantities."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="movements"
    )
    batch = models.ForeignKey(
        StockBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movements",
    )
    movement_type = models.CharField(max_length=10, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    signed_quantity = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    reason = models.CharField(max_length=255, blank=True)
    treatment = models.ForeignKey(
        "fieldbook.Treatment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )

    def save(self, *args, **kwargs):
        sign = Decimal("-1") if self.movement_type == MovementType.OUT else Decimal("1")
        self.signed_quantity = sign * self.quantity
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.movement_type} {self.quantity} {self.product.unit} — {self.product}"
