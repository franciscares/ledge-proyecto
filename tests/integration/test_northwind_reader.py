from app.repositories.northwind_reader import fetch_raw_order_lines, fetch_raw_orders


def test_fetch_raw_orders_from_northwind():
    orders = fetch_raw_orders(limit=2)

    assert len(orders) == 2
    assert "OrderID" in orders[0]
    assert "CustomerID" in orders[0]


def test_fetch_raw_order_lines_from_northwind():
    orders = fetch_raw_orders(limit=1)
    order_ids = [orders[0]["OrderID"]]

    lines = fetch_raw_order_lines(order_ids=order_ids)

    assert len(lines) > 0
    assert lines[0]["OrderID"] == order_ids[0]
    assert "ProductID" in lines[0]
