from rest_framework.routers import DefaultRouter

from apps.farms.views import (
    CampaignViewSet,
    CropViewSet,
    FarmViewSet,
    HarvestRecordViewSet,
    ParcelViewSet,
    SectorViewSet,
)

router = DefaultRouter()
router.register("campaigns", CampaignViewSet, basename="campaign")
router.register("farms", FarmViewSet, basename="farm")
router.register("parcels", ParcelViewSet, basename="parcel")
router.register("sectors", SectorViewSet, basename="sector")
router.register("crops", CropViewSet, basename="crop")
router.register("harvests", HarvestRecordViewSet, basename="harvest")

urlpatterns = router.urls
