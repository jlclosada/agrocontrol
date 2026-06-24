from rest_framework.routers import DefaultRouter

from apps.tenants.views import CooperativeViewSet, MembershipViewSet

router = DefaultRouter()
router.register("cooperatives", CooperativeViewSet, basename="cooperative")
router.register("members", MembershipViewSet, basename="member")

urlpatterns = router.urls
