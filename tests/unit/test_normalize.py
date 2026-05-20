from datetime import date
from decimal import Decimal

from app.domain.models import OrderStatus
from app.pipeline.normalize import normalize_orders


def test_normalize_order_from_raw_northwind_shape():
    raw_orders = [
        {
            "OrderID": 10248,
            "CustomerID": "VINET",
            "CustomerName": "Vins et alcools Chevalier",
            "OrderDate": "1996-07-04",
            "RequiredDate": "1996-08-01",
            "ShippedDate": "1996-07-16",
            "Freight": 32.38,
        }
    ]

    raw_lines = [
        {
            "OrderID": 10248,
            "ProductID": 11,
            "ProductName": "Queso Cabrales",
            "UnitPrice": 14,
            "Quantity": 12,
            "Discount": 0,
        },
        {
            "OrderID": 10248,
            "ProductID": 42,
            "ProductName": "Singaporean Hokkien Fried Mee",
            "UnitPrice": 9.8,
            "Quantity": 10,
            "Discount": 0,
        },
    ]

    orders = normalize_orders(raw_orders, raw_lines)

    assert len(orders) == 1

    order = orders[0]

    assert order.natural_key == "northwind:10248"
    assert order.source_order_id == 10248
    assert order.customer_id == "VINET"
    assert order.order_date == date(1996, 7, 4)
    assert order.required_date == date(1996, 8, 1)
    assert order.shipped_date == date(1996, 7, 16)
    assert order.status == OrderStatus.SHIPPED
    assert order.currency == "USD"
    assert order.freight_amount == Decimal("32.38")

    assert len(order.lines) == 2
    assert order.lines[0].natural_line_key == "northwind:10248:11"
    assert order.lines[0].line_total == Decimal("168.00")

    assert order.subtotal_amount == Decimal("266.00")
    assert order.total_amount == Decimal("298.38")


def test_normalize_pending_order_when_shipped_date_is_null():
    raw_orders = [
        {
            "OrderID": 11000,
            "CustomerID": "ALFKI",
            "CustomerName": "Alfreds Futterkiste",
            "OrderDate": "1998-01-01",
            "RequiredDate": "1998-01-15",
            "ShippedDate": None,
            "Freight": 10,
        }
    ]

    raw_lines = [
        {
            "OrderID": 11000,
            "ProductID": 1,
            "ProductName": "Chai",
            "UnitPrice": 18,
            "Quantity": 2,
            "Discount": 0.1,
        }
    ]

    orders = normalize_orders(raw_orders, raw_lines)

    assert orders[0].status == OrderStatus.PENDING_SHIPMENT
    assert orders[0].shipped_date is None
    assert orders[0].lines[0].line_subtotal == Decimal("36.00")
    assert orders[0].lines[0].line_discount == Decimal("3.60")
    assert orders[0].lines[0].line_total == Decimal("32.40")
