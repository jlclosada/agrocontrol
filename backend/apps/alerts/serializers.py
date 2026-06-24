from rest_framework import serializers

from apps.alerts.models import Alert, AlertRule


class AlertRuleSerializer(serializers.ModelSerializer):
    trigger_display = serializers.CharField(
        source="get_trigger_display", read_only=True
    )

    class Meta:
        model = AlertRule
        fields = [
            "id", "name", "trigger", "trigger_display", "condition",
            "severity", "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AlertSerializer(serializers.ModelSerializer):
    trigger_display = serializers.CharField(
        source="get_trigger_display", read_only=True
    )

    class Meta:
        model = Alert
        fields = [
            "id", "rule", "trigger", "trigger_display", "severity", "title",
            "message", "context", "dedupe_key", "acknowledged", "resolved",
            "created_at",
        ]
        read_only_fields = [
            "id", "rule", "trigger", "severity", "title", "message",
            "context", "dedupe_key", "created_at",
        ]
