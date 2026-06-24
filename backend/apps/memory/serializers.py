from rest_framework import serializers

from apps.memory.models import MemoryEntry


class MemoryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoryEntry
        fields = [
            "id", "scope", "user", "parcel", "crop", "key", "content",
            "data", "tags", "importance", "source", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
