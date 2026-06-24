from apps.common.viewsets import TenantScopedViewSet
from apps.memory.models import MemoryEntry
from apps.memory.serializers import MemoryEntrySerializer


class MemoryEntryViewSet(TenantScopedViewSet):
    serializer_class = MemoryEntrySerializer
    queryset = MemoryEntry.objects.all()
    filterset_fields = ["scope", "user", "parcel", "crop", "source"]
    search_fields = ["content", "key"]
