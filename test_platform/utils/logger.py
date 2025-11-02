"""Logging configuration utilities.

Provides structured JSON logging in production, and human-readable logs in development.
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any, Dict

from config.settings import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logger(name: str) -> logging.Logger:
    """Create and configure a logger.

    - JSON format in production
    - Human-readable in development
    - Level from settings.debug
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = logging.DEBUG if settings.debug else logging.INFO
    logger.setLevel(level)

    handler = logging.StreamHandler(stream=sys.stdout)

    if settings.is_production:
        handler.setFormatter(JsonFormatter())
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    return logger
