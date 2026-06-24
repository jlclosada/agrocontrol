"""Connects domain events to subscribed agents (event-driven agent triggers)."""
import logging

from django.dispatch import receiver

from apps.fieldbook.signals import treatment_registered

logger = logging.getLogger(__name__)


@receiver(treatment_registered)
def on_treatment_registered(sender, instance, **kwargs):
    """Fan out the event to any agent subscribed to 'treatment_registered'."""
    from apps.agents.tasks import dispatch_event_to_agents

    payload = {
        "treatment_id": str(instance.id),
        "product": instance.product.name,
        "crop": str(instance.crop),
        "date": str(instance.date),
        "total_quantity": float(instance.total_quantity),
    }
    try:
        dispatch_event_to_agents.delay(
            "treatment_registered", str(instance.cooperative_id), payload
        )
    except Exception:  # noqa: BLE001 — never let async dispatch break a domain write
        logger.exception("Failed to enqueue treatment_registered event")
