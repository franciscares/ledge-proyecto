from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Literal
from uuid import uuid4

from app.domain.models import CanonicalOrder, PipelineException
from app.pipeline.dedupe import canonical_order_hash


PersistResult = Literal["inserted", "updated", "skipped"]


def create_ingestion_run(conn: sqlite3.Connection, correlation_id: str) -> str:
    run_id = str(uuid4())

    conn.execute(
        """
        INSERT INTO ingestion_runs (
            id,
            correlation_id,
            status,
            started_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            run_id,
            correlation_id,
            "running",
            datetime.utcnow().isoformat(),
        ),
    )

    return run_id


def finish_ingestion_run(
    conn: sqlite3.Connection,
    run_id: str,
    *,
    status: str,
    inserted_count: int,
    updated_count: int,
    skipped_count: int,
    exception_count: int,
) -> None:
    conn.execute(
        """
        UPDATE ingestion_runs
        SET
            status = ?,
            finished_at = ?,
            inserted_count = ?,
            updated_count = ?,
            skipped_count = ?,
            exception_count = ?
        WHERE id = ?
        """,
        (
            status,
            datetime.utcnow().isoformat(),
            inserted_count,
            updated_count,
            skipped_count,
            exception_count,
            run_id,
        ),
    )


def persist_order(
    conn: sqlite3.Connection,
    order: CanonicalOrder,
    *,
    ingestion_run_id: str,
) -> PersistResult:
    content_hash = canonical_order_hash(order)

    existing = conn.execute(
        """
        SELECT id, content_hash
        FROM canonical_orders
        WHERE natural_key = ?
        """,
        (order.natural_key,),
    ).fetchone()

    if existing and existing["content_hash"] == content_hash:
        return "skipped"

    if existing:
        order_id = existing["id"]

        conn.execute(
            """
            UPDATE canonical_orders
            SET
                source_order_id = ?,
                customer_id = ?,
                customer_name = ?,
                order_date = ?,
                required_date = ?,
                shipped_date = ?,
                status = ?,
                currency = ?,
                freight_amount = ?,
                subtotal_amount = ?,
                discount_amount = ?,
                total_amount = ?,
                content_hash = ?,
                ingestion_run_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            _order_values(order, content_hash, ingestion_run_id) + (order_id,),
        )

        conn.execute(
            "DELETE FROM canonical_order_lines WHERE order_id = ?",
            (order_id,),
        )

        _insert_order_lines(conn, order_id, order)

        return "updated"

    order_id = str(uuid4())

    conn.execute(
        """
        INSERT INTO canonical_orders (
            id,
            natural_key,
            source_order_id,
            customer_id,
            customer_name,
            order_date,
            required_date,
            shipped_date,
            status,
            currency,
            freight_amount,
            subtotal_amount,
            discount_amount,
            total_amount,
            content_hash,
            ingestion_run_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (order_id, order.natural_key) +
        _order_values(order, content_hash, ingestion_run_id),
    )

    _insert_order_lines(conn, order_id, order)

    return "inserted"


def persist_exceptions(
    conn: sqlite3.Connection,
    exceptions: list[PipelineException],
    *,
    ingestion_run_id: str,
) -> None:
    for exception in exceptions:
        conn.execute(
            """
            INSERT INTO order_exceptions (
                id,
                ingestion_run_id,
                natural_key,
                stage,
                reason_code,
                message,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                ingestion_run_id,
                exception.natural_key,
                exception.stage,
                exception.reason_code,
                exception.message,
                json.dumps(exception.payload, sort_keys=True, default=str),
            ),
        )


def count_orders(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM canonical_orders").fetchone()
    return int(row["count"])


def count_exceptions(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM order_exceptions").fetchone()
    return int(row["count"])


def get_latest_ingestion_runs(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM ingestion_runs
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    return [dict(row) for row in rows]


def _order_values(
    order: CanonicalOrder,
    content_hash: str,
    ingestion_run_id: str,
) -> tuple:
    return (
        order.source_order_id,
        order.customer_id,
        order.customer_name,
        order.order_date.isoformat(),
        order.required_date.isoformat() if order.required_date else None,
        order.shipped_date.isoformat() if order.shipped_date else None,
        order.status.value,
        order.currency,
        str(order.freight_amount),
        str(order.subtotal_amount),
        str(order.discount_amount),
        str(order.total_amount),
        content_hash,
        ingestion_run_id,
    )


def _insert_order_lines(
    conn: sqlite3.Connection,
    order_id: str,
    order: CanonicalOrder,
) -> None:
    for line in order.lines:
        conn.execute(
            """
            INSERT INTO canonical_order_lines (
                id,
                order_id,
                natural_line_key,
                product_id,
                product_name,
                quantity,
                unit_price,
                discount_rate,
                line_subtotal,
                line_discount,
                line_total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                order_id,
                line.natural_line_key,
                line.product_id,
                line.product_name,
                line.quantity,
                str(line.unit_price),
                str(line.discount_rate),
                str(line.line_subtotal),
                str(line.line_discount),
                str(line.line_total),
            ),
        )


def list_orders(
    conn: sqlite3.Connection,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
) -> list[dict]:
    query = """
        SELECT
            id,
            natural_key,
            source_order_id,
            customer_id,
            customer_name,
            order_date,
            required_date,
            shipped_date,
            status,
            currency,
            freight_amount,
            subtotal_amount,
            discount_amount,
            total_amount,
            content_hash,
            ingestion_run_id,
            created_at,
            updated_at
        FROM canonical_orders
    """

    params: list = []

    if status is not None:
        query += " WHERE status = ?"
        params.append(status)

    query += " ORDER BY source_order_id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_order_by_natural_key(
    conn: sqlite3.Connection,
    natural_key: str,
) -> dict | None:
    order = conn.execute(
        """
        SELECT *
        FROM canonical_orders
        WHERE natural_key = ?
        """,
        (natural_key,),
    ).fetchone()

    if order is None:
        return None

    lines = conn.execute(
        """
        SELECT
            natural_line_key,
            product_id,
            product_name,
            quantity,
            unit_price,
            discount_rate,
            line_subtotal,
            line_discount,
            line_total
        FROM canonical_order_lines
        WHERE order_id = ?
        ORDER BY product_id
        """,
        (order["id"],),
    ).fetchall()

    order_dict = dict(order)
    order_dict["lines"] = [dict(line) for line in lines]

    return order_dict


def list_exceptions(
    conn: sqlite3.Connection,
    *,
    limit: int = 50,
    offset: int = 0,
    reason_code: str | None = None,
    stage: str | None = None,
) -> list[dict]:
    query = """
        SELECT
            id,
            ingestion_run_id,
            natural_key,
            stage,
            reason_code,
            message,
            payload_json,
            created_at
        FROM order_exceptions
    """

    conditions = []
    params: list = []

    if reason_code is not None:
        conditions.append("reason_code = ?")
        params.append(reason_code)

    if stage is not None:
        conditions.append("stage = ?")
        params.append(stage)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]
