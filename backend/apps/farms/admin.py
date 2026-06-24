from django.contrib import admin

from apps.farms.models import Campaign, Crop, Farm, HarvestRecord, Parcel, Sector


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["label", "cooperative", "start_date", "end_date", "is_closed"]
    list_filter = ["cooperative", "is_closed"]
    search_fields = ["label"]


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "cooperative", "created_at"]
    search_fields = ["name"]
    list_filter = ["cooperative"]


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ["name", "farm", "area_ha", "sigpac_ref", "is_active"]
    search_fields = ["name", "sigpac_ref"]
    list_filter = ["cooperative", "is_active"]


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ["name", "parcel", "area_ha"]
    search_fields = ["name"]
    list_filter = ["cooperative"]


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ["species", "variety", "campaign", "parcel", "status"]
    search_fields = ["species", "variety"]
    list_filter = ["cooperative", "status", "campaign"]


@admin.register(HarvestRecord)
class HarvestRecordAdmin(admin.ModelAdmin):
    list_display = ["crop", "date", "quantity_kg", "quality_grade"]
    list_filter = ["cooperative", "date"]
