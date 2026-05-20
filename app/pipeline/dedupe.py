import hashlib
import json
from collections import OrderedDict

from app.domain.models import CanonicalOrder, PipelineException


def canonical_order_hash(order: CanonicalOrder) -> str:
    """
    Creates a deterministic hash from the canonical order payload.

    We use Pydantic's JSON mode so Decimal/date/Enum values become stable
    JSON-compatible values, then sort keys before hashing.
    """
    payload = order.model_dump(mode="json")

    normalized_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(normalized_json.encode("utf-8")).hexdigest()


def dedupe_orders(
    orders: list[CanonicalOrder],
) -> tuple[list[CanonicalOrder], list[PipelineException]]:
    """
    Removes duplicate orders within the same batch.

    If the same natural_key appears with the same hash, keep the first one.
    If the same natural_key appears with a different hash, emit an exception.
    """
    seen: OrderedDict[str, str] = OrderedDict()
    unique_orders_by_key: OrderedDict[str, CanonicalOrder] = OrderedDict()
    exceptions: list[PipelineException] = []

    for order in orders:
        content_hash = canonical_order_hash(order)

        if order.natural_key not in seen:
            seen[order.natural_key] = content_hash
            unique_orders_by_key[order.natural_key] = order
            continue

        previous_hash = seen[order.natural_key]

        if previous_hash == content_hash:
            continue

        exceptions.append(
            PipelineException(
                natural_key=order.natural_key,
                stage="dedupe",
                reason_code="DUPLICATE_NATURAL_KEY_CONFLICT",
                message="Duplicate natural key found with different canonical payload.",
                payload={
                    "natural_key": order.natural_key,
                    "previous_hash": previous_hash,
                    "current_hash": content_hash,
                },
            )
        )

    return list(unique_orders_by_key.values()), exceptions
