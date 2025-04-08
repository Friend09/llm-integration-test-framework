"""Configuration module for LLM Integration Test Framework.

This module handles loading configuration from environment variables and
configuration files, providing a consistent interface for the application.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Union

from dotenv import load_dotenv


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str
    api_key: str
    model: str
    temperature: float = 0.2
    max_tokens: int = 4000
    timeout: float = 60.0


@dataclass(frozen=True)
class ScannerConfig:
    """Configuration for code scanner."""
    temp_dir: Path
    exclude_patterns: list[str]
    max_file_size: int = 5 * 1024 * 1024  # 5MB


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration."""
    llm: LLMConfig
    scanner: ScannerConfig
    output_dir: Path
    log_level: str
    debug: bool = False


def load_config() -> AppConfig:
    """Load application configuration from environment variables and .env file.

    Returns:
        AppConfig: The application configuration object.

    Raises:
        ValueError: If required environment variables are missing.
    """
    # Load environment variables from .env file if it exists
    load_dotenv()

    # LLM configuration
    llm_provider = os.environ.get("LLM_PROVIDER", "openai")
    llm_api_key = os.environ.get("OPENAI_API_KEY")

    if not llm_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    llm_model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    llm_temperature = float(os.environ.get("LLM_TEMPERATURE", "0.2"))
    llm_max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "4000"))
    llm_timeout = float(os.environ.get("LLM_TIMEOUT", "60.0"))

    llm_config = LLMConfig(
        provider=llm_provider,
        api_key=llm_api_key,
        model=llm_model,
        temperature=llm_temperature,
        max_tokens=llm_max_tokens,
        timeout=llm_timeout
    )

    # Scanner configuration
    temp_dir = Path(os.environ.get("TEMP_DIR", "./temp_repos"))
    exclude_patterns = os.environ.get("EXCLUDE_PATTERNS", "node_modules,__pycache__,venv,.git").split(",")
    max_file_size = int(os.environ.get("MAX_FILE_SIZE", str(5 * 1024 * 1024)))  # Default: 5MB

    scanner_config = ScannerConfig(
        temp_dir=temp_dir,
        exclude_patterns=exclude_patterns,
        max_file_size=max_file_size
    )

    # App configuration
    output_dir = Path(os.environ.get("OUTPUT_DIR", "./reports"))
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    return AppConfig(
        llm=llm_config,
        scanner=scanner_config,
        output_dir=output_dir,
        log_level=log_level,
        debug=debug
    )
