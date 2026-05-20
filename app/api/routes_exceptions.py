from fastapi import APIRouter, Query, Depends

from app.api.auth import require_api_key
from app.db import get_connection
from app.repositories.order_repository import list_exceptions

router = APIRouter(
    prefix="/exceptions",
    tags=["exceptions"],
    dependencies=[Depends(require_api_key)],
)


@router.get("")
def get_exceptions(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    reason_code: str | None = None,
    stage: str | None = None,
) -> dict:
    with get_connection() as conn:
        exceptions = list_exceptions(
            conn,
            limit=limit,
            offset=offset,
            reason_code=reason_code,
            stage=stage,
        )

    return {
        "count": len(exceptions),
        "limit": limit,
        "offset": offset,
        "exceptions": exceptions,
    }
