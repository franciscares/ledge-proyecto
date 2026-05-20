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
```
## Modelo canónico

El pipeline transforma los datos crudos de Northwind en un modelo canónico propio compuesto por `CanonicalOrder` y `CanonicalOrderLine`.

Ejemplo:

```json
{
  "natural_key": "northwind:10248",
  "source_order_id": 10248,
  "customer_id": "VINET",
  "customer_name": "Vins et alcools Chevalier",
  "order_date": "1996-07-04",
  "required_date": "1996-08-01",
  "shipped_date": "1996-07-16",
  "status": "shipped",
  "currency": "USD",
  "freight_amount": "32.38",
  "subtotal_amount": "266.00",
  "discount_amount": "0.00",
  "total_amount": "298.38",
  "lines": [
    {
      "natural_line_key": "northwind:10248:11",
      "product_id": 11,
      "product_name": "Queso Cabrales",
      "quantity": 12,
      "unit_price": "14.00",
      "discount_rate": "0.00",
      "line_subtotal": "168.00",
      "line_discount": "0.00",
      "line_total": "168.00"
    }
  ]
}
```

Decisiones:
- Se usa `Decimal` para montos.
- Se usa `date` para fechas.
- La moneda se fija como `USD` porque Northwind no provee moneda explícita.
- `freight_amount` vive a nivel orden y no en líneas.
- `status` se deriva de `shipped_date`.

## Supuestos:
- Las órdenes con inconsistencias de negocio no se persisten como confirmadas; se envían a la cola de excepciones.
- Northwind contiene fechas en formatos date y datetime. El modelo canónico conserva solo la fecha porque el dominio pedido es Orden/Línea y no requiere granularidad horaria.
- Se considera anomalía revisable cuando el flete supera el 50% del total neto de ítems. No implica corrupción de datos, pero se expone como excepción operacional porque Northwind no provee reglas logísticas explícitas.

## Idempotencia y deduplicación

La clave natural de una orden se define como `northwind:{OrderID}`. Para cada orden normalizada se calcula un `content_hash` SHA-256 a partir del JSON canónico ordenado.

La estrategia es:

- `natural_key` nueva: insertar.
- `natural_key` existente con mismo `content_hash`: omitir como ya procesada.
- `natural_key` existente con distinto `content_hash`: actualizar dentro de una transacción o registrar conflicto, según la etapa de persistencia.

Dentro de una misma corrida, el pipeline elimina duplicados exactos y envía a excepciones los duplicados con misma clave natural pero distinto contenido.