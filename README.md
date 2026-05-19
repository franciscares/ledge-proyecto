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

# Northwind Canonical Orders Pipeline

Servicio pequeño para ingerir órdenes desde Northwind SQLite, transformarlas a un modelo canónico propio, correr validaciones/reglas de negocio, persistir resultados en una base versionada y exponer consultas por API.

## Fuente Northwind + verificación

La fuente obligatoria es una referencia fija de Northwind SQLite:

```bash
./scripts/download_northwind.sh
./scripts/verify_northwind.sh