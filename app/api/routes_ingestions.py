from fastapi import APIRouter, Query, Depends

from app.pipeline.runner import run_pipeline
from app.api.auth import require_api_key

router = APIRouter(
    prefix="/ingestions",
    tags=["ingestions"],
    dependencies=[Depends(require_api_key)],
)


@router.post("")
def create_ingestion(limit: int | None = Query(default=None, ge=1)) -> dict:
    return run_pipeline(limit=limit)
