from fastapi import APIRouter, HTTPException, Query, Depends

from app.api.auth import require_api_key
from app.db import get_connection
from app.repositories.order_repository import get_order_by_natural_key, list_orders

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    dependencies=[Depends(require_api_key)],
)


@router.get("")
def get_orders(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status: str | None = None,
) -> dict:
    with get_connection() as conn:
        orders = list_orders(
            conn,
            limit=limit,
            offset=offset,
            status=status,
        )

    return {
        "count": len(orders),
        "limit": limit,
        "offset": offset,
        "orders": orders,
    }


@router.get("/{natural_key:path}")
def get_order(natural_key: str) -> dict:
    with get_connection() as conn:
        order = get_order_by_natural_key(conn, natural_key)

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return order
