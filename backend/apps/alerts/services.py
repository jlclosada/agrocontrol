"""Alert rule evaluation.

Each trigger has an evaluator that inspects domain state and yields candidate
alerts as ``(dedupe_key, title, message, context)`` tuples. ``raise_alert``
upserts an open alert by ``dedupe_key`` so periodic runs never duplicate.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.alerts.models import Alert, AlertRule, AlertSeverity, AlertTrigger


def _raise_alert(rule, dedupe_key, title, message, context=None):
    alert, _ = Alert.objects.update_or_create(
        cooperative=rule.cooperative,
        dedupe_key=dedupe_key,
        resolved=False,
        defaults={
            "rule": rule,
            "trigger": rule.trigger,
            "severity": rule.severity,
            "title": title,
            "message": message,
            "context": context or {},
        },
    )
    return alert


def _eval_stock(rule):
    from apps.inventory.models import Product

    for product in Product.objects.filter(cooperative=rule.cooperative):
        if product.needs_reorder:
            yield (
                f"stock:{product.id}",
                f"Stock bajo: {product.name}",
                f"Quedan {product.current_stock} {product.unit} "
                f"(nivel de reposición {product.reorder_level}).",
                {"product": str(product.id), "current_stock": str(product.current_stock)},
            )


def _eval_expiry(rule):
    from apps.inventory.models import StockBatch
    from apps.tenants.models import get_settings

    default_days = get_settings(rule.cooperative).expiry_alert_days
    days = int(rule.condition.get("days", default_days))
    limit = timezone.localdate() + timedelta(days=days)
    for batch in StockBatch.objects.filter(
        cooperative=rule.cooperative, expiry_date__isnull=False, expiry_date__lte=limit
    ):
        if batch.quantity <= 0:
            continue
        yield (
            f"expiry:{batch.id}",
            f"Lote próximo a caducar: {batch.product.name}",
            f"El lote {batch.lot or '—'} caduca el {batch.expiry_date} "
            f"({batch.quantity} {batch.product.unit} en stock).",
            {"batch": str(batch.id), "expiry_date": str(batch.expiry_date)},
        )


def _eval_safety(rule):
    from apps.fieldbook.models import Treatment

    for treatment in Treatment.objects.filter(
        cooperative=rule.cooperative, safety_interval_ok=False
    ):
        yield (
            f"safety:{treatment.id}",
            f"Plazo de seguridad incumplido: {treatment.product.name}",
            f"El tratamiento del {treatment.date} en {treatment.crop} no respeta "
            f"el plazo de seguridad antes de la cosecha prevista.",
            {"treatment": str(treatment.id)},
        )


EVALUATORS = {
    AlertTrigger.STOCK: _eval_stock,
    AlertTrigger.EXPIRY: _eval_expiry,
    AlertTrigger.SAFETY: _eval_safety,
}


# Maps a trigger to the cooperative settings flag that enables it.
_TRIGGER_FLAGS = {
    AlertTrigger.STOCK: "stock_alerts_enabled",
    AlertTrigger.EXPIRY: "expiry_alerts_enabled",
    AlertTrigger.SAFETY: "safety_alerts_enabled",
}


def _trigger_enabled(rule) -> bool:
    """Honour the per-cooperative enable flags configured in the admin."""
    from apps.tenants.models import get_settings

    flag = _TRIGGER_FLAGS.get(rule.trigger)
    if flag is None:
        return True
    return getattr(get_settings(rule.cooperative), flag, True)


@transaction.atomic
def evaluate_rule(rule):
    """Evaluate a single rule, raising/refreshing alerts. Returns the list."""
    evaluator = EVALUATORS.get(rule.trigger)
    if evaluator is None or not rule.is_active:
        return []
    if not _trigger_enabled(rule):
        return []
    alerts = []
    for dedupe_key, title, message, context in evaluator(rule):
        alerts.append(_raise_alert(rule, dedupe_key, title, message, context))
    return alerts


def evaluate_cooperative(cooperative):
    """Evaluate every active rule of a cooperative."""
    alerts = []
    for rule in AlertRule.objects.filter(cooperative=cooperative, is_active=True):
        alerts.extend(evaluate_rule(rule))
    return alerts


def ensure_default_rules(cooperative):
    """Create a sensible default rule set for a cooperative (idempotent)."""
    defaults = [
        ("Stock mínimo", AlertTrigger.STOCK, {}, AlertSeverity.MEDIUM),
        ("Caducidad de lotes (30 días)", AlertTrigger.EXPIRY, {"days": 30},
         AlertSeverity.MEDIUM),
        ("Plazo de seguridad", AlertTrigger.SAFETY, {}, AlertSeverity.HIGH),
    ]
    created = []
    for name, trigger, condition, severity in defaults:
        rule, was_created = AlertRule.objects.get_or_create(
            cooperative=cooperative,
            trigger=trigger,
            name=name,
            defaults={"condition": condition, "severity": severity},
        )
        if was_created:
            created.append(rule)
    return created
