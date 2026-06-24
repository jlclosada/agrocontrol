from rest_framework.routers import DefaultRouter

from apps.agents.views import AgentRunViewSet, AgentViewSet

router = DefaultRouter()
router.register("agents", AgentViewSet, basename="agent")
router.register("agent-runs", AgentRunViewSet, basename="agentrun")

urlpatterns = router.urls
