"""Inventory services: FEFO consumption and batch availability.

FEFO (First-Expired, First-Out) consumes stock from the batches that expire
soonest, which is the correct policy for perishable phytosanitary products.
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.inventory.models import MovementType, StockBatch, StockMovement


class InsufficientStock(Exception):
    """Raised when a consumption request exceeds available stock."""


def _batch_quantity(batch) -> Decimal:
    agg = batch.movements.aggregate(total=Sum("signed_quantity"))
    return agg["total"] or Decimal("0")


@transaction.atomic
def consume_fefo(product, quantity, reason="", treatment=None):
    """Consume ``quantity`` of ``product`` across batches, earliest-expiry first.

    Creates one OUT ``StockMovement`` per batch touched. Batches without an
    expiry date are consumed last. Returns the list of created movements.
    Raises :class:`InsufficientStock` if there is not enough stock.
    """
    quantity = Decimal(str(quantity))
    if quantity <= 0:
        return []

    cooperative = product.cooperative
    batches = list(
        StockBatch.objects.select_for_update()
        .filter(cooperative=cooperative, product=product)
        .order_by("expiry_date", "created_at")
    )

    available = sum((_batch_quantity(b) for b in batches), Decimal("0"))
    # Stock not assigned to any batch (legacy/untracked movements).
    unbatched = (
        StockMovement.objects.filter(
            cooperative=cooperative, product=product, batch__isnull=True
        ).aggregate(total=Sum("signed_quantity"))["total"]
        or Decimal("0")
    )
    if available + unbatched < quantity:
        raise InsufficientStock(
            f"Stock insuficiente de {product.name}: "
            f"disponible {available + unbatched} {product.unit}, "
            f"solicitado {quantity}."
        )

    remaining = quantity
    movements = []

    # Order batches so that those with an expiry date come first (FEFO),
    # then unbatched stock, then no-expiry batches.
    def _sort_key(batch):
        return (0, batch.expiry_date) if batch.expiry_date else (1, batch.created_at)

    for batch in sorted(batches, key=_sort_key):
        if remaining <= 0:
            break
        qty = _batch_quantity(batch)
        if qty <= 0:
            continue
        take = min(qty, remaining)
        movements.append(
            StockMovement.objects.create(
                cooperative=cooperative,
                product=product,
                batch=batch,
                movement_type=MovementType.OUT,
                quantity=take,
                reason=reason,
                treatment=treatment,
            )
        )
        remaining -= take

    if remaining > 0:
        # Fall back to unbatched stock.
        movements.append(
            StockMovement.objects.create(
                cooperative=cooperative,
                product=product,
                movement_type=MovementType.OUT,
                quantity=remaining,
                reason=reason,
                treatment=treatment,
            )
        )
        remaining = Decimal("0")

    return movements
