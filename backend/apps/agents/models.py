from django.conf import settings
from django.db import models

from apps.common.models import TenantScopedModel


class AgentType(models.TextChoices):
    AGRONOMIST = "AGRONOMIST", "Agente Agrónomo"
    ADMIN = "ADMIN", "Agente Administrativo"
    COOPERATIVE = "COOPERATIVE", "Agente Cooperativa"
    SUPPORT = "SUPPORT", "Agente de Soporte"


class Agent(TenantScopedModel):
    """A configurable AI agent owned by a cooperative.

    Each agent declares its purpose, the LLM model it uses, a list of *skills*
    (human-readable capabilities), the *tools* it may call, and the domain
    *events* it listens to.
    """

    agent_type = models.CharField(max_length=20, choices=AgentType.choices)
    name = models.CharField(max_length=120)
    purpose = models.TextField()
    model = models.CharField(max_length=60, default="gpt-4o-mini")
    system_prompt = models.TextField()
    skills = models.JSONField(default=list, blank=True)
    tools = models.JSONField(default=list, blank=True, help_text="Registered tool names.")
    listens_to = models.JSONField(
        default=list, blank=True, help_text="Domain events, e.g. ['treatment_registered']."
    )
    is_active = models.BooleanField(default=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["agent_type", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.agent_type})"


class RunStatus(models.TextChoices):
    PENDING = "PENDING", "Pendiente"
    RUNNING = "RUNNING", "Ejecutando"
    COMPLETED = "COMPLETED", "Completado"
    FAILED = "FAILED", "Fallido"


class AgentRun(TenantScopedModel):
    """A single execution of an agent (a conversation turn or background task)."""

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="runs")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="agent_runs",
    )
    status = models.CharField(
        max_length=12, choices=RunStatus.choices, default=RunStatus.PENDING
    )
    input_text = models.TextField()
    output_text = models.TextField(blank=True)
    context = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)
    tokens_used = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"Run {self.id} — {self.agent.name} [{self.status}]"


class MessageRole(models.TextChoices):
    SYSTEM = "system", "system"
    USER = "user", "user"
    ASSISTANT = "assistant", "assistant"
    TOOL = "tool", "tool"


class AgentMessage(TenantScopedModel):
    """A message inside an agent run (full transcript including tool calls)."""

    run = models.ForeignKey(AgentRun, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=12, choices=MessageRole.choices)
    content = models.TextField(blank=True)
    tool_name = models.CharField(max_length=80, blank=True)
    tool_calls = models.JSONField(null=True, blank=True)
    tool_call_id = models.CharField(max_length=80, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["created_at"]
