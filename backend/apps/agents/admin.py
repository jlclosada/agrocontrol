from django.contrib import admin

from apps.agents.models import Agent, AgentMessage, AgentRun


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ["name", "agent_type", "model", "is_active", "cooperative"]
    list_filter = ["cooperative", "agent_type", "is_active"]
    search_fields = ["name", "purpose"]


class AgentMessageInline(admin.TabularInline):
    model = AgentMessage
    extra = 0
    readonly_fields = ["role", "content", "tool_name", "created_at"]


@admin.register(AgentRun)
class AgentRunAdmin(admin.ModelAdmin):
    list_display = ["id", "agent", "status", "user", "tokens_used", "created_at"]
    list_filter = ["cooperative", "status"]
    inlines = [AgentMessageInline]
