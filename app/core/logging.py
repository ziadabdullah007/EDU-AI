"""
EduCore AI Platform — Structured Logging

Configures production-grade structured logging using structlog.
Outputs JSON in production and human-readable text in development.
All log records include timestamp, level, module, and correlation context.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config.settings import get_settings


def _add_app_context(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Add application-level context to every log record.

    Injects the application name and environment into each log entry
    to make filtering easy in log aggregation systems.
    """
    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["env"] = settings.app_env
    event_dict["version"] = settings.app_version
    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up structlog with appropriate processors for the current
    environment. JSON output is used in production; colored text output
    is used in development for readability.

    Call this exactly once at application startup.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level, logging.INFO)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_format == "json":
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.debug else logging.WARNING
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a bound structlog logger for a given module.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A structlog BoundLogger instance.
    """
    return structlog.get_logger(name)
