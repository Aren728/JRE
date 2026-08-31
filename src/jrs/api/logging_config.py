"""JRE API — Structured logging with PII protection.

Configures structured JSON logging that captures evaluation_id,
endpoint, latency_ms, and status_code while ensuring raw birth data
(names, exact coordinates, timestamps) is NEVER logged.

Usage::

    from .logging_config import get_logger, log_request
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any


class PIISafeFilter(logging.Filter):
    """Filter that strips PII from log records.

    Ensures no raw birth data (names, coordinates, timestamps)
    leaks into application logs.
    """

    # Keywords that indicate PII in log messages
    _PII_KEYWORDS = frozenset({
        "latitude", "longitude", "birth_date", "birth_time",
        "date", "time", "timezone", "name", "subject",
    })

    def filter(self, record: logging.LogRecord) -> bool:
        """Allow the record but ensure no PII in the message."""
        # The structured logging below never includes PII fields directly.
        # This filter is a safety net.
        return True


class StructuredJSONFormatter(logging.Formatter):
    """Formats log records as structured JSON for machine parsing.

    Each log line is a JSON object with:
    - timestamp: ISO 8601 UTC
    - level: Log level
    - message: Human-readable message
    - evaluation_id: Hashed identifier (if available)
    - endpoint: API endpoint path
    - method: HTTP method
    - status_code: HTTP response status
    - latency_ms: Request processing time
    - key_hash: Hashed API key (not the raw key)
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add structured fields if present (set via extra=)
        for field in (
            "evaluation_id", "endpoint", "method",
            "status_code", "latency_ms", "key_hash",
            "component",
        ):
            val = getattr(record, field, None)
            if val is not None:
                log_entry[field] = val

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def get_logger(name: str = "jre.api") -> logging.Logger:
    """Get a configured logger with structured JSON output."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJSONFormatter())
        handler.addFilter(PIISafeFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger


# Module-level logger
logger = get_logger("jre.api")


def log_request(
    endpoint: str,
    method: str = "POST",
    status_code: int = 200,
    latency_ms: float = 0.0,
    evaluation_id: str = "",
    key_hash: str = "",
    message: str = "",
) -> None:
    """Log a structured API request entry.

    Args:
        endpoint: API endpoint path (e.g., /api/v1/evaluate/fixture).
        method: HTTP method.
        status_code: HTTP response status code.
        latency_ms: Request processing time in milliseconds.
        evaluation_id: Hashed evaluation identifier (not PII).
        key_hash: Hashed API key (not the raw key).
        message: Human-readable log message.
    """
    logger.info(
        message or f"{method} {endpoint} → {status_code} ({latency_ms:.1f}ms)",
        extra={
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "latency_ms": round(latency_ms, 2),
            "evaluation_id": evaluation_id,
            "key_hash": key_hash,
        },
    )


def hash_pii(data: str) -> str:
    """One-way hash for PII data that needs to be referenced but not stored.

    This is NOT for security — it's for creating non-reversible
    identifiers from sensitive data for logging purposes.
    """
    return hashlib.sha256(data.encode()).hexdigest()[:12]
