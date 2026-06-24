from rest_framework.routers import DefaultRouter

from apps.memory.views import MemoryEntryViewSet

router = DefaultRouter()
router.register("memories", MemoryEntryViewSet, basename="memory")

urlpatterns = router.urls
