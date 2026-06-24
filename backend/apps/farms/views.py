from django.core.cache import cache
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.viewsets import TenantScopedViewSet
from apps.farms.models import Campaign, Crop, Farm, HarvestRecord, Parcel, Sector
from apps.farms.serializers import (
    CampaignSerializer,
    CropSerializer,
    FarmSerializer,
    HarvestRecordSerializer,
    ParcelSerializer,
    SectorSerializer,
)
from apps.farms.services import cadastre
from apps.tenants.models import Role


class CampaignViewSet(TenantScopedViewSet):
    serializer_class = CampaignSerializer
    queryset = Campaign.objects.all()
    filterset_fields = ["is_closed"]
    search_fields = ["label"]


class FarmViewSet(TenantScopedViewSet):
    serializer_class = FarmSerializer
    queryset = Farm.objects.select_related("owner").all()
    filterset_fields = ["owner"]
    search_fields = ["name", "description"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Farmers only see their own holdings; admins/agronomists see all in coop.
        if self.get_role() == Role.FARMER:
            qs = qs.filter(owner=self.request.user)
        return qs

    def perform_create(self, serializer):
        owner = serializer.validated_data.get("owner") or self.request.user
        serializer.save(cooperative=self.get_cooperative(), owner=owner)


class ParcelViewSet(TenantScopedViewSet):
    serializer_class = ParcelSerializer
    queryset = Parcel.objects.select_related("farm").all()
    filterset_fields = ["farm", "is_active", "soil_type"]
    search_fields = ["name", "sigpac_ref"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.get_role() == Role.FARMER:
            qs = qs.filter(farm__owner=self.request.user)
        return qs

    @action(detail=False, methods=["get"], url_path="lookup")
    def lookup(self, request):
        """Resolve a cadastral parcel to official geometry, area & centroid.

        Accepts either ``?ref=<cadastral reference>`` or ``?lat=&lon=`` (a point
        clicked on the map). Public-data autofill so users don't draw plots by
        hand. Results are cached to respect the upstream service.
        """
        ref = (request.query_params.get("ref") or "").strip()
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if not ref and (lat is None or lon is None):
            return Response(
                {"detail": "Indica 'ref' o bien 'lat' y 'lon'."},
                status=400,
            )

        if ref:
            cache_key = f"cadastre:ref:{ref.upper()[:14]}"
        else:
            try:
                lat_f, lon_f = float(lat), float(lon)
            except (TypeError, ValueError):
                return Response({"detail": "Coordenadas inválidas."}, status=400)
            cache_key = f"cadastre:geo:{lat_f:.6f},{lon_f:.6f}"

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        try:
            if ref:
                result = cadastre.lookup_by_reference(ref)
            else:
                result = cadastre.lookup_by_coordinate(lat_f, lon_f)
        except cadastre.CadastreNotFound as exc:
            return Response({"detail": str(exc)}, status=404)
        except cadastre.CadastreError as exc:
            return Response({"detail": str(exc)}, status=502)
        payload = {
            "reference": result["reference"],
            "area_ha": str(result["area_ha"]) if result["area_ha"] is not None else None,
            "polygon": result["polygon"],
            "latitude": str(result["latitude"]) if result["latitude"] is not None else None,
            "longitude": str(result["longitude"]) if result["longitude"] is not None else None,
            "source": result["source"],
        }
        cache.set(cache_key, payload, 60 * 60 * 24)  # 24h
        return Response(payload)


class SectorViewSet(TenantScopedViewSet):
    serializer_class = SectorSerializer
    queryset = Sector.objects.select_related("parcel", "parcel__farm").all()
    filterset_fields = ["parcel"]
    search_fields = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.get_role() == Role.FARMER:
            qs = qs.filter(parcel__farm__owner=self.request.user)
        return qs


class CropViewSet(TenantScopedViewSet):
    serializer_class = CropSerializer
    queryset = Crop.objects.select_related("parcel", "parcel__farm").all()
    filterset_fields = ["parcel", "sector", "season", "status", "campaign", "species"]
    search_fields = ["species", "variety", "campaign"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.get_role() == Role.FARMER:
            qs = qs.filter(parcel__farm__owner=self.request.user)
        return qs


class HarvestRecordViewSet(TenantScopedViewSet):
    serializer_class = HarvestRecordSerializer
    queryset = HarvestRecord.objects.select_related(
        "crop", "crop__parcel", "crop__parcel__farm"
    ).all()
    filterset_fields = ["crop"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.get_role() == Role.FARMER:
            qs = qs.filter(crop__parcel__farm__owner=self.request.user)
        return qs
