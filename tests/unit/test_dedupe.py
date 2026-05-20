from datetime import date
from decimal import Decimal

from app.domain.models import CanonicalOrder, CanonicalOrderLine, OrderStatus
from app.pipeline.dedupe import canonical_order_hash, dedupe_orders


def make_order(
    *,
    natural_key: str = "northwind:10248",
    source_order_id: int = 10248,
    quantity: int = 12,
) -> CanonicalOrder:
    return CanonicalOrder(
        natural_key=natural_key,
        source_order_id=source_order_id,
        customer_id="VINET",
        customer_name="Vins et alcools Chevalier",
        order_date=date(1996, 7, 4),
        required_date=date(1996, 8, 1),
        shipped_date=date(1996, 7, 16),
        status=OrderStatus.SHIPPED,
        freight_amount=Decimal("32.38"),
        lines=[
            CanonicalOrderLine(
                natural_line_key=f"{natural_key}:11",
                product_id=11,
                product_name="Queso Cabrales",
                quantity=quantity,
                unit_price=Decimal("14.00"),
                discount_rate=Decimal("0.00"),
            )
        ],
    )


def test_hash_is_deterministic_for_same_order():
    order = make_order()

    first_hash = canonical_order_hash(order)
    second_hash = canonical_order_hash(order)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_hash_changes_when_order_payload_changes():
    first_order = make_order(quantity=12)
    second_order = make_order(quantity=13)

    assert canonical_order_hash(
        first_order) != canonical_order_hash(second_order)


def test_dedupe_skips_exact_duplicate():
    order = make_order()

    unique_orders, exceptions = dedupe_orders([order, order])

    assert len(unique_orders) == 1
    assert exceptions == []


def test_dedupe_flags_same_natural_key_with_different_payload():
    first_order = make_order(quantity=12)
    second_order = make_order(quantity=13)

    unique_orders, exceptions = dedupe_orders([first_order, second_order])

    assert len(unique_orders) == 1
    assert len(exceptions) == 1
    assert exceptions[0].reason_code == "DUPLICATE_NATURAL_KEY_CONFLICT"
