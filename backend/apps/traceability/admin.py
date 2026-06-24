from django.contrib import admin

from apps.traceability.models import TraceEvent


@admin.register(TraceEvent)
class TraceEventAdmin(admin.ModelAdmin):
    list_display = [
        "sequence", "action", "entity_type", "entity_id", "actor",
        "cooperative", "occurred_at",
    ]
    list_filter = ["cooperative", "action", "entity_type"]
    search_fields = ["entity_id", "hash"]
    readonly_fields = [f.name for f in TraceEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
