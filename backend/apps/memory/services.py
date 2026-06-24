"""MemoryService — the single API agents use to read/write persistent memory.

Designed to be simple now (keyword/tag filtering) but ready to upgrade to
semantic search with pgvector by populating ``embedding`` and swapping ``recall``.
"""
from __future__ import annotations

from typing import Iterable

from django.db.models import Q

from apps.memory.models import MemoryEntry, MemoryScope


class MemoryService:
    def __init__(self, cooperative):
        self.cooperative = cooperative

    # --- write -----------------------------------------------------------
    def remember(
        self,
        scope: str,
        content: str,
        *,
        user=None,
        parcel=None,
        crop=None,
        key: str = "",
        data: dict | None = None,
        tags: Iterable[str] | None = None,
        importance: int = 1,
        source: str = "system",
    ) -> MemoryEntry:
        defaults = {
            "content": content,
            "data": data or {},
            "tags": list(tags or []),
            "importance": importance,
            "source": source,
            "user": user,
            "parcel": parcel,
            "crop": crop,
        }
        if key:
            entry, _ = MemoryEntry.objects.update_or_create(
                cooperative=self.cooperative, scope=scope, key=key, defaults=defaults
            )
            return entry
        return MemoryEntry.objects.create(
            cooperative=self.cooperative, scope=scope, key=key, **defaults
        )

    # --- read ------------------------------------------------------------
    def recall(
        self,
        *,
        scope: str | None = None,
        user=None,
        parcel=None,
        crop=None,
        query: str = "",
        tags: Iterable[str] | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        qs = MemoryEntry.objects.filter(cooperative=self.cooperative)
        if scope:
            qs = qs.filter(scope=scope)
        if user is not None:
            qs = qs.filter(user=user)
        if parcel is not None:
            qs = qs.filter(parcel=parcel)
        if crop is not None:
            qs = qs.filter(crop=crop)
        if query:
            qs = qs.filter(Q(content__icontains=query) | Q(key__icontains=query))
        tag_list = list(tags or [])
        if tag_list:
            # Filtered in Python for cross-DB portability (SQLite has no JSON contains).
            entries = [e for e in qs if all(t in (e.tags or []) for t in tag_list)]
            return entries[:limit]
        return list(qs[:limit])

    def summarize(self, **kwargs) -> str:
        """Compact textual context block to inject into an agent prompt."""
        entries = self.recall(**kwargs)
        if not entries:
            return "No relevant memory."
        return "\n".join(
            f"- ({e.scope}/imp{e.importance}) {e.content}" for e in entries
        )

    # --- convenience helpers --------------------------------------------
    def user_memory(self, user, **kwargs):
        return self.recall(scope=MemoryScope.USER, user=user, **kwargs)

    def parcel_memory(self, parcel=None, crop=None, **kwargs):
        return self.recall(
            scope=MemoryScope.PARCEL, parcel=parcel, crop=crop, **kwargs
        )

    def global_memory(self, **kwargs):
        return self.recall(scope=MemoryScope.GLOBAL, **kwargs)
