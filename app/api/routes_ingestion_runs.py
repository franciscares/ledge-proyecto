from fastapi import APIRouter, Query, Depends

from app.api.auth import require_api_key
from app.db import get_connection
from app.repositories.order_repository import get_latest_ingestion_runs

router = APIRouter(
    prefix="/ingestion-runs",
    tags=["ingestion-runs"],
    dependencies=[Depends(require_api_key)],
)


@router.get("")
def list_ingestion_runs(
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    with get_connection() as conn:
        runs = get_latest_ingestion_runs(conn, limit=limit)

    return {
        "count": len(runs),
        "runs": runs,
    }
