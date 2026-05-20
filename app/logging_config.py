import json
import logging
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_fields"):
            payload.update(record.extra_fields)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def log_info(
    logger: logging.Logger,
    message: str,
    **extra_fields: Any,
) -> None:
    logger.info(
        message,
        extra={
            "extra_fields": extra_fields,
        },
    )


def log_error(
    logger: logging.Logger,
    message: str,
    **extra_fields: Any,
) -> None:
    logger.error(
        message,
        extra={
            "extra_fields": extra_fields,
        },
    )
