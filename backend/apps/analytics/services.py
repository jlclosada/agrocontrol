"""Analytics aggregation service.

KPIs are scoped to the active cooperative and, for FARMER users, further
restricted to their own holdings. All query helpers accept a pre-filtered base
queryset so the role logic lives in one place (:func:`build_dashboard`).
"""
from decimal import Decimal

from django.db.models import Count, Sum

from apps.tenants.models import Role


def _scoped_crops(cooperative, user, role):
    from apps.farms.models import Crop

    qs = Crop.objects.filter(cooperative=cooperative)
    if role == Role.FARMER:
        qs = qs.filter(parcel__farm__owner=user)
    return qs


def build_dashboard(cooperative, user, role):
    """Return a role-aware KPI dashboard for a cooperative."""
    from apps.alerts.models import Alert
    from apps.costs.models import ProfitabilityReport
    from apps.farms.models import Farm, HarvestRecord, Parcel
    from apps.inventory.models import Product

    crops = _scoped_crops(cooperative, user, role)
    crop_ids = list(crops.values_list("id", flat=True))

    farms = Farm.objects.filter(cooperative=cooperative)
    parcels = Parcel.objects.filter(cooperative=cooperative)
    if role == Role.FARMER:
        farms = farms.filter(owner=user)
        parcels = parcels.filter(farm__owner=user)

    total_area = parcels.aggregate(t=Sum("area_ha"))["t"] or Decimal("0")

    harvests = HarvestRecord.objects.filter(crop_id__in=crop_ids)
    total_harvest = harvests.aggregate(t=Sum("quantity_kg"))["t"] or Decimal("0")

    reports = ProfitabilityReport.objects.filter(crop_id__in=crop_ids)
    econ = reports.aggregate(
        cost=Sum("total_cost"), income=Sum("income"), profit=Sum("profit")
    )

    # Alerts are cooperative-wide; only admins/agronomists see them in the KPIs.
    open_alerts = 0
    if role != Role.FARMER:
        open_alerts = Alert.objects.filter(
            cooperative=cooperative, resolved=False
        ).count()

    crops_by_status = list(
        crops.values("status").annotate(count=Count("id")).order_by("status")
    )

    low_stock = 0
    if role != Role.FARMER:
        low_stock = sum(
            1 for p in Product.objects.filter(cooperative=cooperative)
            if p.needs_reorder
        )

    return {
        "cooperative": cooperative.name,
        "role": role,
        "counts": {
            "farms": farms.count(),
            "parcels": parcels.count(),
            "crops": len(crop_ids),
            "total_area_ha": str(total_area),
        },
        "production": {
            "total_harvest_kg": str(total_harvest),
        },
        "economics": {
            "total_cost": str(econ["cost"] or Decimal("0")),
            "total_income": str(econ["income"] or Decimal("0")),
            "total_profit": str(econ["profit"] or Decimal("0")),
        },
        "alerts": {
            "open": open_alerts,
            "low_stock_products": low_stock,
        },
        "crops_by_status": crops_by_status,
    }


def profitability_rows(cooperative, user, role):
    """Flat rows for CSV export of per-crop profitability."""
    from apps.costs.models import ProfitabilityReport

    crops = _scoped_crops(cooperative, user, role)
    crop_ids = list(crops.values_list("id", flat=True))
    reports = (
        ProfitabilityReport.objects.filter(crop_id__in=crop_ids)
        .select_related("crop", "crop__parcel")
        .order_by("crop__species")
    )
    rows = []
    for r in reports:
        rows.append(
            {
                "cultivo": r.crop.species,
                "variedad": r.crop.variety,
                "campaña": r.crop.campaign,
                "parcela": r.crop.parcel.name if r.crop.parcel_id else "",
                "coste_total": r.total_cost,
                "ingreso": r.income,
                "beneficio": r.profit,
                "coste_ha": r.cost_per_ha,
                "margen_pct": r.margin_pct,
            }
        )
    return rows
