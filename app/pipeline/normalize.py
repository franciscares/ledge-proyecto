from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from app.domain.models import CanonicalOrder, CanonicalOrderLine, OrderStatus


def normalize_orders(
    raw_orders: list[dict[str, Any]],
    raw_lines: list[dict[str, Any]],
) -> list[CanonicalOrder]:
    lines_by_order_id: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for line in raw_lines:
        lines_by_order_id[int(line["OrderID"])].append(line)

    canonical_orders: list[CanonicalOrder] = []

    for raw_order in raw_orders:
        source_order_id = int(raw_order["OrderID"])
        order_lines = lines_by_order_id[source_order_id]

        canonical_lines = [
            normalize_order_line(
                source_order_id=source_order_id, raw_line=raw_line)
            for raw_line in order_lines
        ]

        canonical_orders.append(
            CanonicalOrder(
                natural_key=f"northwind:{source_order_id}",
                source_order_id=source_order_id,
                customer_id=raw_order.get("CustomerID"),
                customer_name=raw_order.get("CustomerName"),
                order_date=parse_date(raw_order["OrderDate"]),
                required_date=parse_optional_date(
                    raw_order.get("RequiredDate")),
                shipped_date=parse_optional_date(raw_order.get("ShippedDate")),
                status=derive_status(raw_order.get("ShippedDate")),
                currency="USD",
                freight_amount=to_decimal(raw_order.get("Freight")),
                lines=canonical_lines,
            )
        )

    return canonical_orders


def normalize_order_line(
    source_order_id: int,
    raw_line: dict[str, Any],
) -> CanonicalOrderLine:
    product_id = int(raw_line["ProductID"])

    return CanonicalOrderLine(
        natural_line_key=f"northwind:{source_order_id}:{product_id}",
        product_id=product_id,
        product_name=raw_line.get("ProductName"),
        quantity=int(raw_line["Quantity"]),
        unit_price=to_decimal(raw_line["UnitPrice"]),
        discount_rate=to_decimal(raw_line["Discount"]),
    )


def derive_status(shipped_date: Any) -> OrderStatus:
    if shipped_date:
        return OrderStatus.SHIPPED

    return OrderStatus.PENDING_SHIPMENT


def parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value

    return date.fromisoformat(str(value))


def parse_optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None

    return parse_date(value)


def to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value))
