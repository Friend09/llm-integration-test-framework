"""Logging configuration for the LLM Integration Testing Framework."""

import json
import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.logging import RichHandler


class StructuredLogger:
    """A logger that outputs structured logs in both console and file formats."""

    def __init__(
        self,
        name: str,
        log_dir: Optional[str] = None,
        console_level: str = "INFO",
        file_level: str = "DEBUG",
    ):
        """Initialize the structured logger.

        Args:
            name: Logger name
            log_dir: Directory to store log files (default: logs/)
            console_level: Logging level for console output
            file_level: Logging level for file output
        """
        self.name = name
        self.log_dir = Path(log_dir or "logs")
        self.console_level = getattr(logging, console_level.upper())
        self.file_level = getattr(logging, file_level.upper())

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging configuration
        self._configure_logging()

        # Get logger instance
        self.logger = logging.getLogger(name)

    def _configure_logging(self) -> None:
        """Configure logging with both console and file handlers."""
        # Create console handler with rich formatting
        console = Console(force_terminal=True)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            level=self.console_level,
        )

        # Create file handler with JSON formatting
        log_file = self.log_dir / f"{self.name}_{datetime.now():%Y%m%d}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.file_level)
        file_handler.setFormatter(
            logging.Formatter(
                json.dumps({
                    'timestamp': '%(asctime)s',
                    'name': '%(name)s',
                    'level': '%(levelname)s',
                    'message': '%(message)s',
                    'module': '%(module)s',
                    'function': '%(funcName)s',
                    'line': '%(lineno)d',
                    'extra': '%(extra)s'
                })
            )
        )

        # Configure root logger
        logging.basicConfig(
            level=min(self.console_level, self.file_level),
            format="%(message)s",
            datefmt="[%X]",
            handlers=[console_handler, file_handler],
        )

    def _log(
        self,
        level: int,
        msg: str,
        extra: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs
    ) -> None:
        """Log a message with the specified level and extra context.

        Args:
            level: Logging level
            msg: Message to log
            extra: Additional context to include in the log
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        extra = extra or {}
        self.logger.log(level, msg, extra={'extra': json.dumps(extra)}, *args, **kwargs)

    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None, *args, **kwargs) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, msg, extra, *args, **kwargs)

    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None, *args, **kwargs) -> None:
        """Log an info message."""
        self._log(logging.INFO, msg, extra, *args, **kwargs)

    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None, *args, **kwargs) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, msg, extra, *args, **kwargs)

    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None, *args, **kwargs) -> None:
        """Log an error message."""
        self._log(logging.ERROR, msg, extra, *args, **kwargs)

    def critical(self, msg: str, extra: Optional[Dict[str, Any]] = None, *args, **kwargs) -> None:
        """Log a critical message."""
        self._log(logging.CRITICAL, msg, extra, *args, **kwargs)

    def exception(self, msg: str, extra: Optional[Dict[str, Any]] = None, *args, **kwargs) -> None:
        """Log an exception message with traceback."""
        self._log(logging.ERROR, msg, extra, exc_info=True, *args, **kwargs)


# Create default logger instance
logger = StructuredLogger("llm_integration_test_framework")
