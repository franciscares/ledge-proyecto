from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.models import CanonicalOrder, CanonicalOrderLine, OrderStatus


def test_order_line_computes_totals():
    line = CanonicalOrderLine(
        natural_line_key="northwind:10248:11",
        product_id=11,
        product_name="Queso Cabrales",
        quantity=12,
        unit_price=Decimal("14.00"),
        discount_rate=Decimal("0.00"),
    )

    assert line.line_subtotal == Decimal("168.00")
    assert line.line_discount == Decimal("0.00")
    assert line.line_total == Decimal("168.00")


def test_order_computes_totals_with_freight():
    order = CanonicalOrder(
        natural_key="northwind:10248",
        source_order_id=10248,
        customer_id="VINET",
        customer_name="Vins et alcools Chevalier",
        order_date=date(1996, 7, 4),
        required_date=date(1996, 8, 1),
        shipped_date=date(1996, 7, 16),
        status=OrderStatus.SHIPPED,
        currency="usd",
        freight_amount=Decimal("32.38"),
        lines=[
            CanonicalOrderLine(
                natural_line_key="northwind:10248:11",
                product_id=11,
                product_name="Queso Cabrales",
                quantity=12,
                unit_price=Decimal("14.00"),
                discount_rate=Decimal("0.00"),
            ),
            CanonicalOrderLine(
                natural_line_key="northwind:10248:42",
                product_id=42,
                product_name="Singaporean Hokkien Fried Mee",
                quantity=10,
                unit_price=Decimal("9.80"),
                discount_rate=Decimal("0.00"),
            ),
        ],
    )

    assert order.currency == "USD"
    assert order.subtotal_amount == Decimal("266.00")
    assert order.discount_amount == Decimal("0.00")
    assert order.lines_total_amount == Decimal("266.00")
    assert order.total_amount == Decimal("298.38")


def test_order_line_rejects_invalid_discount():
    with pytest.raises(ValidationError):
        CanonicalOrderLine(
            natural_line_key="northwind:bad:1",
            product_id=1,
            quantity=1,
            unit_price=Decimal("10.00"),
            discount_rate=Decimal("1.50"),
        )


def test_order_rejects_empty_lines():
    with pytest.raises(ValidationError):
        CanonicalOrder(
            natural_key="northwind:empty",
            source_order_id=1,
            order_date=date(1996, 1, 1),
            status=OrderStatus.PENDING_SHIPMENT,
            freight_amount=Decimal("0.00"),
            lines=[],
        )
