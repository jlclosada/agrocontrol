from django.contrib import admin

from apps.alerts.models import Alert, AlertRule


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "trigger", "severity", "is_active", "cooperative"]
    list_filter = ["cooperative", "trigger", "severity", "is_active"]
    search_fields = ["name"]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = [
        "title", "trigger", "severity", "acknowledged", "resolved",
        "cooperative", "created_at",
    ]
    list_filter = ["cooperative", "trigger", "severity", "acknowledged", "resolved"]
    search_fields = ["title", "message"]
