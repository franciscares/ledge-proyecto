from fastapi import FastAPI

from app.api.routes_debug import router as debug_router
from app.config import get_settings
from app.db import apply_migrations
from app.api.routes_ingestions import router as ingestions_router
from app.api.routes_exceptions import router as exceptions_router
from app.api.routes_ingestion_runs import router as ingestion_runs_router
from app.api.routes_orders import router as orders_router
from app.logging_config import configure_logging

settings = get_settings()

app = FastAPI(
    title="Northwind Canonical Orders Pipeline",
    version="0.1.0",
    description="Pipeline service for canonical order ingestion from Northwind SQLite.",
)

configure_logging()


@app.on_event("startup")
def startup() -> None:
    apply_migrations()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
    }


app.include_router(debug_router)
app.include_router(ingestions_router)
app.include_router(orders_router)
app.include_router(exceptions_router)
app.include_router(ingestion_runs_router)
