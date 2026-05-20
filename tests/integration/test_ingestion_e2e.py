from pathlib import Path
import shutil

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import apply_migrations, get_connection
from app.main import app

client = TestClient(app)


def reset_app_db() -> None:
    settings = get_settings()
    db_path = Path(settings.app_db_path)

    if db_path.exists():
        db_path.unlink()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    apply_migrations()


def count_orders_in_db() -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM canonical_orders").fetchone()
        return int(row["count"])


def test_ingestion_is_idempotent_for_same_limit():
    reset_app_db()

    first_response = client.post(
        "/ingestions?limit=10",
        headers={"X-API-Key": "dev-api-key"},
    )

    assert first_response.status_code == 200
    first_payload = first_response.json()

    assert first_payload["status"] == "completed"
    assert first_payload["inserted_count"] == 10
    assert first_payload["skipped_count"] == 0
    assert count_orders_in_db() == 10

    second_response = client.post(
        "/ingestions?limit=10",
        headers={"X-API-Key": "dev-api-key"},
    )

    assert second_response.status_code == 200
    second_payload = second_response.json()

    assert second_payload["status"] == "completed"
    assert second_payload["inserted_count"] == 0
    assert second_payload["skipped_count"] == 10
    assert count_orders_in_db() == 10


def test_orders_api_lists_persisted_orders():
    reset_app_db()

    client.post(
        "/ingestions?limit=5",
        headers={"X-API-Key": "dev-api-key"},
    )

    response = client.get(
        "/orders?limit=5",
        headers={"X-API-Key": "dev-api-key"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["count"] == 5
    assert len(payload["orders"]) == 5
    assert payload["orders"][0]["natural_key"].startswith("northwind:")


def test_api_requires_api_key():
    response = client.get("/orders")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing X-API-Key header"
