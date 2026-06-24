from rest_framework import serializers

from apps.traceability.models import TraceEvent


class TraceEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = TraceEvent
        fields = [
            "id", "sequence", "actor", "actor_email", "entity_type", "entity_id",
            "action", "payload", "occurred_at", "prev_hash", "hash",
        ]
        read_only_fields = fields
