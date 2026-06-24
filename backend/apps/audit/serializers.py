from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    event_display = serializers.CharField(source="get_event_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "event", "event_display", "email", "user", "cooperative",
            "ip_address", "user_agent", "detail", "created_at",
        ]
        read_only_fields = fields
