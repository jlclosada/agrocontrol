"""Auto-capture domain writes into the traceability chain.

Connects to the tracked domain models and records a ``TraceEvent`` on every
create/update/delete. Actor is best-effort: taken from known user fields on the
instance when present (full request-actor capture would require middleware).
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.traceability.models import TraceAction
from apps.traceability.services import record_event

# Fields, per model, that we snapshot into the event payload.
_TRACKED = {
    "farms.Crop": ["species", "variety", "campaign", "status", "expected_yield_kg"],
    "farms.HarvestRecord": ["date", "quantity_kg", "quality_grade"],
    "fieldbook.FieldOperation": ["operation_type", "date", "description", "area_ha"],
    "fieldbook.Treatment": [
        "date", "dose", "dose_unit", "total_quantity", "target_pest",
        "safety_interval_ok",
    ],
    "inventory.StockMovement": ["movement_type", "quantity", "signed_quantity", "reason"],
}

_ACTOR_FIELDS = ("performed_by", "applicator", "actor", "owner")


def _label(instance) -> str:
    meta = instance._meta
    return f"{meta.app_label}.{meta.object_name}"


def _actor(instance):
    for field in _ACTOR_FIELDS:
        value = getattr(instance, f"{field}_id", None)
        if value:
            return getattr(instance, field, None)
    return None


def _payload(instance, fields) -> dict:
    data = {}
    for field in fields:
        data[field] = getattr(instance, field, None)
    return data


def _handle(instance, action):
    label = _label(instance)
    fields = _TRACKED.get(label)
    if fields is None:
        return
    cooperative = getattr(instance, "cooperative", None)
    if cooperative is None:
        return
    record_event(
        cooperative=cooperative,
        entity_type=instance._meta.object_name,
        entity_id=instance.pk,
        action=action,
        payload=_payload(instance, fields),
        actor=_actor(instance),
    )


@receiver(post_save)
def on_save(sender, instance, created, **kwargs):
    if _label(instance) not in _TRACKED:
        return
    _handle(instance, TraceAction.CREATE if created else TraceAction.UPDATE)


@receiver(post_delete)
def on_delete(sender, instance, **kwargs):
    if _label(instance) not in _TRACKED:
        return
    _handle(instance, TraceAction.DELETE)
