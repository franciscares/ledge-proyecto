from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Northwind Canonical Orders Pipeline",
    version="0.1.0",
    description="Pipeline service for canonical order ingestion from Northwind SQLite.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
    }
