CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT,
    inserted_count INTEGER NOT NULL DEFAULT 0,
    updated_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    exception_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS canonical_orders (
    id TEXT PRIMARY KEY,
    natural_key TEXT NOT NULL UNIQUE,
    source_order_id INTEGER NOT NULL,
    customer_id TEXT,
    customer_name TEXT,
    order_date TEXT,
    required_date TEXT,
    shipped_date TEXT,
    status TEXT NOT NULL,
    currency TEXT NOT NULL,
    freight_amount TEXT NOT NULL,
    subtotal_amount TEXT NOT NULL,
    discount_amount TEXT NOT NULL,
    total_amount TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    ingestion_run_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(id)
);

CREATE TABLE IF NOT EXISTS canonical_order_lines (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    natural_line_key TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT,
    quantity INTEGER NOT NULL,
    unit_price TEXT NOT NULL,
    discount_rate TEXT NOT NULL,
    line_subtotal TEXT NOT NULL,
    line_discount TEXT NOT NULL,
    line_total TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(order_id, natural_line_key),
    FOREIGN KEY (order_id) REFERENCES canonical_orders(id)
);

CREATE TABLE IF NOT EXISTS order_exceptions (
    id TEXT PRIMARY KEY,
    ingestion_run_id TEXT NOT NULL,
    natural_key TEXT,
    stage TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    message TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_canonical_orders_natural_key
ON canonical_orders(natural_key);

CREATE INDEX IF NOT EXISTS idx_order_exceptions_reason_code
ON order_exceptions(reason_code);

CREATE INDEX IF NOT EXISTS idx_order_exceptions_stage
ON order_exceptions(stage);