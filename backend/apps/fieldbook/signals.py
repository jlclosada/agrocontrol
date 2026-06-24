"""Domain signals for the field notebook.

When a treatment is registered we automatically:
1. Create an OUT stock movement so inventory stays consistent.
2. Emit a domain event that AI agents can subscribe to (e.g. the Agronomist
   checking safety intervals, or the Cooperative agent updating dashboards).
"""
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

from apps.fieldbook.models import Treatment

# Generic domain event other apps (agents) can connect to.
treatment_registered = Signal()  # providing_args: instance


@receiver(post_save, sender=Treatment)
def consume_stock_on_treatment(sender, instance: Treatment, created, **kwargs):
    if not created:
        return

    from apps.inventory.services import InsufficientStock, consume_fefo

    already = instance.stock_movements.exists()
    if not already and instance.total_quantity:
        try:
            consume_fefo(
                product=instance.product,
                quantity=instance.total_quantity,
                reason=f"Tratamiento {instance.id}",
                treatment=instance,
            )
        except InsufficientStock:
            # Record the consumption anyway so the field notebook stays truthful;
            # the resulting negative balance surfaces as a low-stock alert.
            from apps.inventory.models import MovementType, StockMovement

            StockMovement.objects.create(
                cooperative=instance.cooperative,
                product=instance.product,
                movement_type=MovementType.OUT,
                quantity=instance.total_quantity,
                reason=f"Tratamiento {instance.id} (sin lote / stock negativo)",
                treatment=instance,
            )

    treatment_registered.send(sender=Treatment, instance=instance)
