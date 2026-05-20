import logging
from uuid import uuid4

from app.db import get_connection
from app.pipeline.consistency import run_consistency_checks
from app.pipeline.dedupe import dedupe_orders
from app.pipeline.normalize import normalize_orders
from app.repositories.northwind_reader import fetch_raw_order_lines, fetch_raw_orders
from app.repositories.order_repository import (
    create_ingestion_run,
    finish_ingestion_run,
    persist_exceptions,
    persist_order,
)
from app.logging_config import log_error, log_info

logger = logging.getLogger(__name__)


def run_pipeline(limit: int | None = None) -> dict:
    correlation_id = str(uuid4())

    log_info(
        logger,
        "pipeline_started",
        event="pipeline_started",
        correlation_id=correlation_id,
        limit=limit,
    )

    with get_connection() as conn:
        run_id = create_ingestion_run(conn, correlation_id)

        try:
            raw_orders = fetch_raw_orders(limit=limit)
            order_ids = [order["OrderID"] for order in raw_orders]
            raw_lines = fetch_raw_order_lines(order_ids=order_ids)

            log_info(
                logger,
                "pipeline_stage_completed",
                event="pipeline_stage_completed",
                correlation_id=correlation_id,
                stage="ingest",
                raw_orders_count=len(raw_orders),
                raw_lines_count=len(raw_lines),
            )

            canonical_orders = normalize_orders(raw_orders, raw_lines)

            log_info(
                logger,
                "pipeline_stage_completed",
                event="pipeline_stage_completed",
                correlation_id=correlation_id,
                stage="normalize",
                input_count=len(raw_orders),
                output_count=len(canonical_orders),
            )

            deduped_orders, dedupe_exceptions = dedupe_orders(canonical_orders)

            log_info(
                logger,
                "pipeline_stage_completed",
                event="pipeline_stage_completed",
                correlation_id=correlation_id,
                stage="dedupe",
                input_count=len(canonical_orders),
                output_count=len(deduped_orders),
                exception_count=len(dedupe_exceptions),
            )

            valid_orders, consistency_exceptions = run_consistency_checks(
                deduped_orders)

            log_info(
                logger,
                "pipeline_stage_completed",
                event="pipeline_stage_completed",
                correlation_id=correlation_id,
                stage="consistency-checks",
                input_count=len(deduped_orders),
                output_count=len(valid_orders),
                exception_count=len(consistency_exceptions),
            )

            exceptions = [*dedupe_exceptions, *consistency_exceptions]

            inserted_count = 0
            updated_count = 0
            skipped_count = 0

            for order in valid_orders:
                result = persist_order(
                    conn,
                    order,
                    ingestion_run_id=run_id,
                )

                if result == "inserted":
                    inserted_count += 1
                elif result == "updated":
                    updated_count += 1
                elif result == "skipped":
                    skipped_count += 1

            persist_exceptions(
                conn,
                exceptions,
                ingestion_run_id=run_id,
            )

            log_info(
                logger,
                "pipeline_stage_completed",
                event="pipeline_stage_completed",
                correlation_id=correlation_id,
                stage="persist",
                inserted_count=inserted_count,
                updated_count=updated_count,
                skipped_count=skipped_count,
                exception_count=len(exceptions),
            )

            finish_ingestion_run(
                conn,
                run_id,
                status="completed",
                inserted_count=inserted_count,
                updated_count=updated_count,
                skipped_count=skipped_count,
                exception_count=len(exceptions),
            )

            conn.commit()

            summary = {
                "run_id": run_id,
                "correlation_id": correlation_id,
                "status": "completed",
                "input_orders_count": len(canonical_orders),
                "deduped_orders_count": len(deduped_orders),
                "valid_orders_count": len(valid_orders),
                "inserted_count": inserted_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "exception_count": len(exceptions),
            }

            log_info(
                logger,
                "pipeline_completed",
                event="pipeline_completed",
                **summary,
            )

            return summary

        except Exception as exc:
            finish_ingestion_run(
                conn,
                run_id,
                status="failed",
                inserted_count=0,
                updated_count=0,
                skipped_count=0,
                exception_count=0,
            )
            conn.commit()

            log_error(
                logger,
                "pipeline_failed",
                event="pipeline_failed",
                correlation_id=correlation_id,
                error=str(exc),
            )

            raise
