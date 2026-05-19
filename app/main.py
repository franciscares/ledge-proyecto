from fastapi import FastAPI

from app.config import get_settings
from app.db import apply_migrations

settings = get_settings()

app = FastAPI(
    title="Northwind Canonical Orders Pipeline",
    version="0.1.0",
    description="Pipeline service for canonical order ingestion from Northwind SQLite.",
)


@app.on_event("startup")
def startup() -> None:
    apply_migrations()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
    }
