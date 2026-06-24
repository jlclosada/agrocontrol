from celery import shared_task


@shared_task
def evaluate_cooperative_alerts(cooperative_id: str):
    """Evaluate all active alert rules for a single cooperative."""
    from apps.alerts.services import evaluate_cooperative
    from apps.tenants.models import Cooperative

    cooperative = Cooperative.objects.get(id=cooperative_id)
    alerts = evaluate_cooperative(cooperative)
    return len(alerts)


@shared_task
def evaluate_all_alerts():
    """Periodic entrypoint: fan out evaluation across active cooperatives."""
    from apps.tenants.models import Cooperative

    count = 0
    for coop_id in Cooperative.objects.filter(is_active=True).values_list(
        "id", flat=True
    ):
        evaluate_cooperative_alerts.delay(str(coop_id))
        count += 1
    return count
