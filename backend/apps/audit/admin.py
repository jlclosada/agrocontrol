from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["event", "email", "user", "cooperative", "ip_address", "created_at"]
    list_filter = ["event", "cooperative", "created_at"]
    search_fields = ["email", "detail", "ip_address"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
