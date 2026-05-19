from pathlib import Path
import shutil
import sqlite3
from typing import Any

from app.config import get_settings


def prepare_runtime_northwind_copy() -> Path:
    """
    Copies the raw Northwind DB into a runtime location.

    The raw DB is treated as immutable. The application reads from the runtime
    copy so the source reference is never mutated by mistake.
    """
    settings = get_settings()

    raw_path = Path(settings.raw_db_path)
    runtime_path = Path(settings.runtime_db_path)

    if not raw_path.exists():
        raise FileNotFoundError(
            f"Northwind DB not found at {raw_path}. "
            "Run ./scripts/download_northwind.sh first."
        )

    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(raw_path, runtime_path)

    return runtime_path


def get_northwind_connection() -> sqlite3.Connection:
    """
    Opens the runtime Northwind DB in read-only mode.
    """
    runtime_path = prepare_runtime_northwind_copy()

    uri = f"file:{runtime_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_raw_orders(limit: int | None = None) -> list[dict[str, Any]]:
    """
    Fetches raw Northwind orders with customer and shipper information.

    This function intentionally returns raw dictionaries. Canonical conversion
    happens later in the normalize stage.
    """
    query = """
        SELECT
            o.OrderID,
            o.CustomerID,
            c.CompanyName AS CustomerName,
            o.EmployeeID,
            o.OrderDate,
            o.RequiredDate,
            o.ShippedDate,
            o.ShipVia,
            s.CompanyName AS ShipperName,
            o.Freight,
            o.ShipName,
            o.ShipAddress,
            o.ShipCity,
            o.ShipRegion,
            o.ShipPostalCode,
            o.ShipCountry
        FROM Orders o
        LEFT JOIN Customers c ON c.CustomerID = o.CustomerID
        LEFT JOIN Shippers s ON s.ShipperID = o.ShipVia
        ORDER BY o.OrderID
    """

    params: tuple[Any, ...] = ()

    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    with get_northwind_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def fetch_raw_order_lines(order_ids: list[int] | None = None) -> list[dict[str, Any]]:
    """
    Fetches raw Northwind order lines with product information.
    """
    query = """
        SELECT
            od.OrderID,
            od.ProductID,
            p.ProductName,
            od.UnitPrice,
            od.Quantity,
            od.Discount
        FROM "Order Details" od
        LEFT JOIN Products p ON p.ProductID = od.ProductID
    """

    params: list[Any] = []

    if order_ids:
        placeholders = ",".join(["?"] * len(order_ids))
        query += f" WHERE od.OrderID IN ({placeholders})"
        params.extend(order_ids)

    query += " ORDER BY od.OrderID, od.ProductID"

    with get_northwind_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]
