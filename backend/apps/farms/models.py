from django.conf import settings
from django.db import models

from apps.common.models import TenantScopedModel


class Campaign(TenantScopedModel):
    """An agricultural season/campaign that groups crops (e.g. 2025/2026).

    Closing a campaign freezes its crops for reporting and traceability.
    """

    label = models.CharField(max_length=20, help_text="e.g. 2025/2026")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

    class Meta(TenantScopedModel.Meta):
        ordering = ["-label"]
        constraints = [
            models.UniqueConstraint(
                fields=["cooperative", "label"], name="unique_campaign_per_coop"
            )
        ]

    def __str__(self) -> str:
        return self.label


class Farm(TenantScopedModel):
    """An agricultural holding (explotación) owned/managed by a farmer."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="farms",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Parcel(TenantScopedModel):
    """A field/plot. ``sigpac_ref`` is the cadastral reference used in the EU."""

    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="parcels")
    name = models.CharField(max_length=200)
    sigpac_ref = models.CharField("SIGPAC reference", max_length=120, blank=True)
    area_ha = models.DecimalField("area (ha)", max_digits=10, decimal_places=4)
    soil_type = models.CharField(max_length=120, blank=True)
    province = models.CharField(max_length=120, blank=True)
    municipality = models.CharField(max_length=160, blank=True)
    address = models.CharField("location/address", max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    polygon = models.JSONField(
        null=True, blank=True,
        help_text="GeoJSON-like list of [lon, lat] points delimiting the parcel.",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.area_ha} ha)"


class Sector(TenantScopedModel):
    """A subdivision of a parcel for finer-grained management.

    A parcel can hold several crops at once, so it's digitised into zones
    (sectors). ``polygon`` stores the drawn geometry and ``color`` distinguishes
    zones on the map.
    """

    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name="sectors")
    name = models.CharField(max_length=200)
    area_ha = models.DecimalField("area (ha)", max_digits=10, decimal_places=4)
    color = models.CharField(
        max_length=9, blank=True,
        help_text="Hex color used to render the zone on the map.",
    )
    polygon = models.JSONField(
        null=True, blank=True,
        help_text="GeoJSON-like list of [lon, lat] points delimiting the zone.",
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.parcel.name})"


class CropStatus(models.TextChoices):
    PLANNED = "PLANNED", "Planificado"
    GROWING = "GROWING", "En crecimiento"
    HARVESTED = "HARVESTED", "Cosechado"
    FAILED = "FAILED", "Fallido"


class Crop(TenantScopedModel):
    """A crop grown on a parcel during a campaign/season."""

    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name="crops")
    sector = models.ForeignKey(
        Sector, on_delete=models.SET_NULL, null=True, blank=True, related_name="crops"
    )
    species = models.CharField(max_length=120)
    variety = models.CharField(max_length=120, blank=True)
    campaign = models.CharField(max_length=20, help_text="e.g. 2025/2026")
    season = models.ForeignKey(
        Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name="crops"
    )
    sowing_date = models.DateField(null=True, blank=True)
    expected_harvest_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=CropStatus.choices, default=CropStatus.PLANNED
    )
    expected_yield_kg = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    def __str__(self) -> str:
        return f"{self.species} {self.variety} — {self.campaign}"


class HarvestRecord(TenantScopedModel):
    """A harvest event for a crop, capturing yield and quality."""

    crop = models.ForeignKey(
        Crop, on_delete=models.CASCADE, related_name="harvests"
    )
    date = models.DateField()
    quantity_kg = models.DecimalField(max_digits=12, decimal_places=2)
    quality_grade = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Quality score/grade (e.g. % or rendimiento graso).",
    )
    price_per_kg = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        help_text="Sale price per kg, used to compute crop income.",
    )
    notes = models.TextField(blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.quantity_kg} kg — {self.crop} ({self.date})"
