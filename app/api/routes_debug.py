from fastapi import APIRouter, Depends

from app.api.auth import require_api_key
from app.pipeline.normalize import normalize_orders
from app.repositories.northwind_reader import fetch_raw_order_lines, fetch_raw_orders
from app.pipeline.consistency import run_consistency_checks
from app.pipeline.dedupe import dedupe_orders
from app.pipeline.dedupe import canonical_order_hash, dedupe_orders

router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/northwind/orders")
def debug_northwind_orders(limit: int = 5) -> dict:
    orders = fetch_raw_orders(limit=limit)
    order_ids = [order["OrderID"] for order in orders]
    lines = fetch_raw_order_lines(order_ids=order_ids)

    return {
        "orders_count": len(orders),
        "lines_count": len(lines),
        "orders": orders,
        "lines": lines[:20],
    }


@router.get("/canonical/orders")
def debug_canonical_orders(limit: int = 5) -> dict:
    raw_orders = fetch_raw_orders(limit=limit)
    order_ids = [order["OrderID"] for order in raw_orders]
    raw_lines = fetch_raw_order_lines(order_ids=order_ids)

    canonical_orders = normalize_orders(raw_orders, raw_lines)

    return {
        "orders_count": len(canonical_orders),
        "orders": [
            order.model_dump(mode="json")
            for order in canonical_orders
        ],
    }


@router.get("/pipeline/checks")
def debug_pipeline_checks(limit: int = 5) -> dict:
    raw_orders = fetch_raw_orders(limit=limit)
    order_ids = [order["OrderID"] for order in raw_orders]
    raw_lines = fetch_raw_order_lines(order_ids=order_ids)

    canonical_orders = normalize_orders(raw_orders, raw_lines)

    deduped_orders, dedupe_exceptions = dedupe_orders(canonical_orders)
    valid_orders, consistency_exceptions = run_consistency_checks(
        deduped_orders)

    exceptions = [*dedupe_exceptions, *consistency_exceptions]

    return {
        "input_orders_count": len(canonical_orders),
        "deduped_orders_count": len(deduped_orders),
        "valid_orders_count": len(valid_orders),
        "exceptions_count": len(exceptions),
        "sample_exceptions": [
            exception.model_dump(mode="json")
            for exception in exceptions[:20]
        ],
    }


@router.get("/canonical/orders/{source_order_id}/hash")
def debug_order_hash(source_order_id: int) -> dict:
    raw_orders = fetch_raw_orders(limit=None)
    raw_orders = [
        order
        for order in raw_orders
        if int(order["OrderID"]) == source_order_id
    ]

    if not raw_orders:
        return {
            "found": False,
            "source_order_id": source_order_id,
        }

    raw_lines = fetch_raw_order_lines(order_ids=[source_order_id])
    canonical_order = normalize_orders(raw_orders, raw_lines)[0]

    return {
        "found": True,
        "natural_key": canonical_order.natural_key,
        "content_hash": canonical_order_hash(canonical_order),
        "order": canonical_order.model_dump(mode="json"),
    }
