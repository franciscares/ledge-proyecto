from fastapi import APIRouter

from app.repositories.northwind_reader import fetch_raw_order_lines, fetch_raw_orders

router = APIRouter(prefix="/debug", tags=["debug"])


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
