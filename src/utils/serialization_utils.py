"""Utilities for data serialization and deserialization."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel

from src.utils.file_utils import safe_read_file, safe_write_file
from src.utils.logging import logger


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj: Any) -> Any:
        """Convert datetime objects to ISO format strings.

        Args:
            obj: Object to encode

        Returns:
            JSON-serializable object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


def to_json(
    data: Any,
    indent: Optional[int] = 2,
    sort_keys: bool = True,
    ensure_ascii: bool = False
) -> str:
    """Convert data to JSON string.

    Args:
        data: Data to convert
        indent: Number of spaces for indentation (None for compact)
        sort_keys: Whether to sort dictionary keys
        ensure_ascii: Whether to escape non-ASCII characters

    Returns:
        JSON string representation

    Raises:
        TypeError: If data is not JSON-serializable
    """
    try:
        if isinstance(data, BaseModel):
            data = data.model_dump()
        return json.dumps(
            data,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
            cls=DateTimeEncoder
        )
    except TypeError as e:
        logger.error("Failed to serialize to JSON", extra={"error": str(e)})
        raise


def from_json(data: str) -> Any:
    """Parse JSON string to Python object.

    Args:
        data: JSON string to parse

    Returns:
        Parsed Python object

    Raises:
        json.JSONDecodeError: If JSON is invalid
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON", extra={"error": str(e)})
        raise


def save_json(
    data: Any,
    path: Union[str, Path],
    indent: Optional[int] = 2,
    sort_keys: bool = True,
    ensure_ascii: bool = False
) -> None:
    """Save data to JSON file.

    Args:
        data: Data to save
        path: Path to save to
        indent: Number of spaces for indentation
        sort_keys: Whether to sort dictionary keys
        ensure_ascii: Whether to escape non-ASCII characters

    Raises:
        TypeError: If data is not JSON-serializable
        IOError: If file writing fails
    """
    json_str = to_json(data, indent, sort_keys, ensure_ascii)
    safe_write_file(path, json_str)


def load_json(path: Union[str, Path]) -> Any:
    """Load data from JSON file.

    Args:
        path: Path to load from

    Returns:
        Parsed Python object

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        IOError: If file reading fails
    """
    json_str = safe_read_file(path)
    return from_json(json_str)


def to_yaml(
    data: Any,
    default_flow_style: bool = False,
    sort_keys: bool = True
) -> str:
    """Convert data to YAML string.

    Args:
        data: Data to convert
        default_flow_style: Use flow style for collections
        sort_keys: Whether to sort dictionary keys

    Returns:
        YAML string representation

    Raises:
        yaml.YAMLError: If data cannot be serialized to YAML
    """
    try:
        if isinstance(data, BaseModel):
            data = data.model_dump()
        return yaml.safe_dump(
            data,
            default_flow_style=default_flow_style,
            sort_keys=sort_keys,
            allow_unicode=True
        )
    except yaml.YAMLError as e:
        logger.error("Failed to serialize to YAML", extra={"error": str(e)})
        raise


def from_yaml(data: str) -> Any:
    """Parse YAML string to Python object.

    Args:
        data: YAML string to parse

    Returns:
        Parsed Python object

    Raises:
        yaml.YAMLError: If YAML is invalid
    """
    try:
        return yaml.safe_load(data)
    except yaml.YAMLError as e:
        logger.error("Failed to parse YAML", extra={"error": str(e)})
        raise


def save_yaml(
    data: Any,
    path: Union[str, Path],
    default_flow_style: bool = False,
    sort_keys: bool = True
) -> None:
    """Save data to YAML file.

    Args:
        data: Data to save
        path: Path to save to
        default_flow_style: Use flow style for collections
        sort_keys: Whether to sort dictionary keys

    Raises:
        yaml.YAMLError: If data cannot be serialized to YAML
        IOError: If file writing fails
    """
    yaml_str = to_yaml(data, default_flow_style, sort_keys)
    safe_write_file(path, yaml_str)


def load_yaml(path: Union[str, Path]) -> Any:
    """Load data from YAML file.

    Args:
        path: Path to load from

    Returns:
        Parsed Python object

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
        IOError: If file reading fails
    """
    yaml_str = safe_read_file(path)
    return from_yaml(yaml_str)
