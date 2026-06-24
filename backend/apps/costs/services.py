"""Cost imputation and profitability computation.

Auto-imputation is idempotent: each treatment/operation maps to at most one
auto cost entry (enforced by a DB constraint on ``treatment`` plus a lookup for
operations), so signals and the management command can run repeatedly.
"""
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.costs.models import (
    CostCategory,
    CostEntry,
    CostSource,
    ProfitabilityReport,
)

# Default labour cost per field operation when no machinery/labour detail exists.
DEFAULT_OPERATION_LABOR_COST = Decimal("25.00")


def impute_treatment_cost(treatment):
    """Create/update the PRODUCT cost entry derived from a treatment."""
    unit_cost = treatment.product.unit_cost or Decimal("0")
    amount = (unit_cost * (treatment.total_quantity or Decimal("0"))).quantize(
        Decimal("0.01")
    )
    entry, _ = CostEntry.objects.update_or_create(
        treatment=treatment,
        defaults={
            "cooperative": treatment.cooperative,
            "crop": treatment.crop,
            "category": CostCategory.PRODUCT,
            "source": CostSource.TREATMENT,
            "amount": amount,
            "date": treatment.date,
            "description": f"Producto: {treatment.product.name}",
        },
    )
    return entry


def impute_operation_cost(operation, amount=None):
    """Create/update a LABOR cost entry derived from a field operation.

    When no explicit amount is given, the cooperative's configured default
    operation cost is used (admin-configurable, falls back to 25.00).
    """
    if amount is None:
        from apps.tenants.models import get_settings

        amount = get_settings(operation.cooperative).default_operation_cost
    entry, _ = CostEntry.objects.update_or_create(
        operation=operation,
        source=CostSource.OPERATION,
        defaults={
            "cooperative": operation.cooperative,
            "crop": operation.crop,
            "category": CostCategory.LABOR,
            "amount": Decimal(amount).quantize(Decimal("0.01")),
            "date": operation.date,
            "description": f"Mano de obra: {operation.get_operation_type_display()}",
        },
    )
    return entry


@transaction.atomic
def compute_profitability(crop):
    """Aggregate costs and harvest income into a ProfitabilityReport."""
    from django.db.models import Sum

    total_cost = crop.cost_entries.aggregate(t=Sum("amount"))["t"] or Decimal("0")

    income = Decimal("0")
    for harvest in crop.harvests.all():
        if harvest.price_per_kg:
            income += (harvest.quantity_kg or Decimal("0")) * harvest.price_per_kg
    income = income.quantize(Decimal("0.01"))

    profit = (income - total_cost).quantize(Decimal("0.01"))

    area = _crop_area(crop)
    cost_per_ha = (
        (total_cost / area).quantize(Decimal("0.01")) if area else Decimal("0")
    )
    margin_pct = (
        (profit / income * Decimal("100")).quantize(Decimal("0.01"))
        if income
        else Decimal("0")
    )

    report, _ = ProfitabilityReport.objects.update_or_create(
        crop=crop,
        defaults={
            "cooperative": crop.cooperative,
            "total_cost": total_cost,
            "income": income,
            "profit": profit,
            "cost_per_ha": cost_per_ha,
            "margin_pct": margin_pct,
            "computed_at": timezone.now(),
        },
    )
    return report


def _crop_area(crop):
    """Best-effort cultivated area in ha: sector, else parcel."""
    if crop.sector_id and crop.sector.area_ha:
        return crop.sector.area_ha
    if crop.parcel_id and crop.parcel.area_ha:
        return crop.parcel.area_ha
    return None
