from rest_framework import serializers

from apps.farms.models import Campaign, Crop, Farm, HarvestRecord, Parcel, Sector


class CampaignSerializer(serializers.ModelSerializer):
    crops_count = serializers.IntegerField(source="crops.count", read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id", "label", "start_date", "end_date", "is_closed",
            "crops_count", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class FarmSerializer(serializers.ModelSerializer):
    parcels_count = serializers.IntegerField(source="parcels.count", read_only=True)

    class Meta:
        model = Farm
        fields = ["id", "owner", "name", "description", "parcels_count", "created_at"]
        read_only_fields = ["id", "created_at"]


class ParcelSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source="farm.name", read_only=True)

    class Meta:
        model = Parcel
        fields = [
            "id", "farm", "farm_name", "name", "sigpac_ref", "area_ha",
            "soil_type", "province", "municipality", "address",
            "latitude", "longitude", "polygon", "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SectorSerializer(serializers.ModelSerializer):
    parcel_name = serializers.CharField(source="parcel.name", read_only=True)
    crops_count = serializers.IntegerField(source="crops.count", read_only=True)

    class Meta:
        model = Sector
        fields = [
            "id", "parcel", "parcel_name", "name", "area_ha",
            "color", "polygon", "crops_count", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CropSerializer(serializers.ModelSerializer):
    parcel_name = serializers.CharField(source="parcel.name", read_only=True)
    season_label = serializers.CharField(source="season.label", read_only=True)

    class Meta:
        model = Crop
        fields = [
            "id", "parcel", "parcel_name", "sector", "species", "variety",
            "campaign", "season", "season_label", "sowing_date",
            "expected_harvest_date", "status", "expected_yield_kg", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class HarvestRecordSerializer(serializers.ModelSerializer):
    crop_label = serializers.CharField(source="crop.__str__", read_only=True)

    class Meta:
        model = HarvestRecord
        fields = [
            "id", "crop", "crop_label", "date", "quantity_kg",
            "quality_grade", "price_per_kg", "notes", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
