# ledge-proyecto

## Tecnologías:
* Backend: Python + FastAPI
* Base propia: SQLite o Postgres
* Migraciones: Alembic si usas SQLAlchemy, o archivos SQL versionados si quieres algo más simple
* Tests: pytest
* CLI opcional: Typer, solo si no quieres REST
* Ejecución: Docker Compose
* Logs: JSON con structlog o logging estándar formateado
* OpenAPI: FastAPI lo entrega automáticamente