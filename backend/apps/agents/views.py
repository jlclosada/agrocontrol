from rest_framework.decorators import action
from rest_framework.response import Response

from apps.agents.models import Agent, AgentRun
from apps.agents.runtime import AgentRuntime
from apps.agents.serializers import (
    AgentRunSerializer,
    AgentSerializer,
    ChatRequestSerializer,
)
from apps.agents.tasks import run_agent_task
from apps.common.viewsets import TenantScopedViewSet


class AgentViewSet(TenantScopedViewSet):
    serializer_class = AgentSerializer
    queryset = Agent.objects.all()
    filterset_fields = ["agent_type", "is_active"]
    search_fields = ["name", "purpose"]

    @action(detail=True, methods=["post"])
    def chat(self, request, pk=None):
        """Send a message to this agent and get a (sync or async) response."""
        agent = self.get_object()
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]
        run_async = serializer.validated_data["async_run"]

        if run_async:
            run = AgentRun.objects.create(
                cooperative=self.get_cooperative(),
                agent=agent,
                user=request.user,
                input_text=message,
            )
            run_agent_task.delay(str(run.id))
            return Response(AgentRunSerializer(run).data, status=202)

        runtime = AgentRuntime(
            agent=agent,
            user=request.user,
            cooperative=self.get_cooperative(),
            role=self.get_role(),
        )
        run = runtime.run(message)
        return Response(AgentRunSerializer(run).data)


class AgentRunViewSet(TenantScopedViewSet):
    serializer_class = AgentRunSerializer
    queryset = AgentRun.objects.select_related("agent").prefetch_related("messages")
    filterset_fields = ["agent", "status"]
    http_method_names = ["get", "head", "options"]
