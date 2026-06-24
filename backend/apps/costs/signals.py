"""Auto-impute costs when treatments and field operations are recorded."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.fieldbook.models import FieldOperation, Treatment


@receiver(post_save, sender=Treatment)
def impute_on_treatment(sender, instance, created, **kwargs):
    from apps.costs.services import impute_treatment_cost

    impute_treatment_cost(instance)


@receiver(post_save, sender=FieldOperation)
def impute_on_operation(sender, instance, created, **kwargs):
    # Treatments carry their own PRODUCT cost; skip the linked operation to
    # avoid double-counting labour on top of the treatment row.
    if hasattr(instance, "treatment") and instance.treatment is not None:
        return
    from apps.costs.services import impute_operation_cost

    impute_operation_cost(instance)
