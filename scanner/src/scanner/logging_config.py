"""Logging configuration."""

import logging
import logging.handlers
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger


def setup_logging(
    level: str = "INFO", format_type: str = "json", log_file: Optional[str] = None
) -> None:
    """Configure logging for the scanner.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ("json" or "text")
        log_file: Optional file path for logging
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create handler(s)
    handlers: list[logging.Handler] = []

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    handlers.append(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setLevel(numeric_level)
        handlers.append(file_handler)

    # Configure formatters
    if format_type == "json":
        # JSON formatter
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            timestamp=True,
        )
        for handler in handlers:
            handler.setFormatter(formatter)
    else:
        # Text formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        for handler in handlers:
            handler.setFormatter(formatter)

    # Add handlers to root logger
    for handler in handlers:
        root_logger.addHandler(handler)

    # Set specific log levels for noisy libraries
    logging.getLogger("bleak").setLevel(logging.WARNING)
    logging.getLogger("paho").setLevel(logging.WARNING)
