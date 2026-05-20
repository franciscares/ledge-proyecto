from datetime import date
from decimal import Decimal

from app.domain.models import CanonicalOrder, CanonicalOrderLine, OrderStatus
from app.domain.rules import run_business_rules


def make_order(
    *,
    required_date: date | None = date(1996, 8, 1),
    shipped_date: date | None = date(1996, 7, 16),
    discount_rate: Decimal = Decimal("0.00"),
    freight_amount: Decimal = Decimal("10.00"),
) -> CanonicalOrder:
    return CanonicalOrder(
        natural_key="northwind:10248",
        source_order_id=10248,
        customer_id="VINET",
        customer_name="Vins et alcools Chevalier",
        order_date=date(1996, 7, 4),
        required_date=required_date,
        shipped_date=shipped_date,
        status=OrderStatus.SHIPPED if shipped_date else OrderStatus.PENDING_SHIPMENT,
        freight_amount=freight_amount,
        lines=[
            CanonicalOrderLine(
                natural_line_key="northwind:10248:11",
                product_id=11,
                product_name="Queso Cabrales",
                quantity=12,
                unit_price=Decimal("14.00"),
                discount_rate=discount_rate,
            )
        ],
    )


def test_required_date_before_order_date_is_exception():
    order = make_order(required_date=date(1996, 7, 1))

    exceptions = run_business_rules(order)

    assert len(exceptions) == 1
    assert exceptions[0].reason_code == "REQUIRED_DATE_BEFORE_ORDER_DATE"


def test_shipped_date_before_order_date_is_exception():
    order = make_order(shipped_date=date(1996, 7, 1))

    exceptions = run_business_rules(order)

    assert len(exceptions) == 1
    assert exceptions[0].reason_code == "SHIPPED_DATE_BEFORE_ORDER_DATE"


def test_high_discount_is_exception():
    order = make_order(discount_rate=Decimal("0.75"))

    exceptions = run_business_rules(order)

    assert len(exceptions) == 1
    assert exceptions[0].reason_code == "HIGH_DISCOUNT"


def test_valid_order_has_no_exceptions():
    order = make_order()

    exceptions = run_business_rules(order)

    assert exceptions == []


def test_freight_too_high_vs_items_is_exception():
    order = CanonicalOrder(
        natural_key="northwind:freight-high",
        source_order_id=999,
        customer_id="TEST",
        customer_name="Test Customer",
        order_date=date(1996, 7, 4),
        required_date=date(1996, 8, 1),
        shipped_date=date(1996, 7, 16),
        status=OrderStatus.SHIPPED,
        freight_amount=Decimal("100.00"),
        lines=[
            CanonicalOrderLine(
                natural_line_key="northwind:freight-high:1",
                product_id=1,
                product_name="Cheap Item",
                quantity=1,
                unit_price=Decimal("100.00"),
                discount_rate=Decimal("0.00"),
            )
        ],
    )

    exceptions = run_business_rules(order)

    assert len(exceptions) == 1
    assert exceptions[0].reason_code == "FREIGHT_TOO_HIGH_VS_ITEMS"
