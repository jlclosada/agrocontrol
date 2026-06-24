from rest_framework import serializers

from apps.agents.models import Agent, AgentMessage, AgentRun


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = [
            "id", "agent_type", "name", "purpose", "model", "system_prompt",
            "skills", "tools", "listens_to", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AgentMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentMessage
        fields = ["id", "role", "content", "tool_name", "tool_calls", "created_at"]
        read_only_fields = fields


class AgentRunSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.name", read_only=True)
    messages = AgentMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AgentRun
        fields = [
            "id", "agent", "agent_name", "user", "status", "input_text",
            "output_text", "error", "tokens_used", "messages", "created_at",
        ]
        read_only_fields = fields


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    async_run = serializers.BooleanField(default=False)
