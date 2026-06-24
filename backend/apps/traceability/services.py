"""Hash-chain service for tamper-evident traceability.

The canonical hash of an event is::

    sha256(prev_hash + canonical_json(sequence, entity_type, entity_id,
                                      action, payload, occurred_at))

Because each hash includes the previous one, altering any historical event
invalidates every later hash, which :func:`verify_chain` detects.
"""
import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.traceability.models import TraceEvent


def _json_default(value):
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def canonical_json(data) -> str:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), default=_json_default
    )


def compute_hash(prev_hash, sequence, entity_type, entity_id, action, payload, occurred_at):
    body = canonical_json(
        {
            "sequence": sequence,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "action": action,
            "payload": payload,
            "occurred_at": occurred_at.isoformat()
            if hasattr(occurred_at, "isoformat")
            else str(occurred_at),
        }
    )
    return hashlib.sha256((prev_hash + body).encode("utf-8")).hexdigest()


@transaction.atomic
def record_event(cooperative, entity_type, entity_id, action, payload, actor=None):
    """Append a new event to the cooperative chain (race-safe)."""
    last = (
        TraceEvent.objects.select_for_update()
        .filter(cooperative=cooperative)
        .order_by("-sequence")
        .first()
    )
    prev_hash = last.hash if last else ""
    sequence = (last.sequence + 1) if last else 1
    occurred_at = timezone.now()

    safe_payload = json.loads(canonical_json(payload))
    digest = compute_hash(
        prev_hash, sequence, entity_type, entity_id, action, safe_payload, occurred_at
    )

    return TraceEvent.objects.create(
        cooperative=cooperative,
        sequence=sequence,
        actor=actor,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        payload=safe_payload,
        occurred_at=occurred_at,
        prev_hash=prev_hash,
        hash=digest,
    )


def verify_chain(cooperative):
    """Recompute the chain and return its integrity status.

    Returns a dict: ``{"valid": bool, "count": int, "broken_at": int | None}``.
    """
    events = TraceEvent.objects.filter(cooperative=cooperative).order_by("sequence")
    prev_hash = ""
    count = 0
    for event in events.iterator():
        expected = compute_hash(
            prev_hash,
            event.sequence,
            event.entity_type,
            event.entity_id,
            event.action,
            event.payload,
            event.occurred_at,
        )
        if expected != event.hash or event.prev_hash != prev_hash:
            return {"valid": False, "count": count, "broken_at": event.sequence}
        prev_hash = event.hash
        count += 1
    return {"valid": True, "count": count, "broken_at": None}
