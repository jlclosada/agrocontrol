from django.contrib import admin

from apps.memory.models import MemoryEntry


@admin.register(MemoryEntry)
class MemoryEntryAdmin(admin.ModelAdmin):
    list_display = ["scope", "key", "importance", "source", "cooperative", "created_at"]
    list_filter = ["cooperative", "scope", "source"]
    search_fields = ["content", "key"]
