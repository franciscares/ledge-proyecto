from pathlib import Path
import sqlite3

from app.config import get_settings


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    db_path = Path(settings.app_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def apply_migrations() -> None:
    migrations_dir = Path("migrations")

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        migration_files = sorted(migrations_dir.glob("*.sql"))

        for migration_file in migration_files:
            version = migration_file.stem

            already_applied = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (version,),
            ).fetchone()

            if already_applied:
                continue

            sql = migration_file.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (version,),
            )

        conn.commit()
