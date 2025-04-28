"""Utilities for input validation and type checking."""

import re
from pathlib import Path
from typing import Any, List, Optional, Pattern, Type, TypeVar, Union
from urllib.parse import urlparse

from src.utils.logging import logger

T = TypeVar("T")

# Common validation patterns
URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP address
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$", re.IGNORECASE
)

GITHUB_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?github\.com/"  # GitHub domain
    r"[A-Za-z0-9_.-]+/"  # username/organization
    r"[A-Za-z0-9_.-]+/?$"  # repository
)

EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def validate_type(value: Any, expected_type: Type[T], name: str = "value") -> T:
    """Validate that a value is of the expected type.

    Args:
        value: Value to validate
        expected_type: Expected type
        name: Name of the value for error messages

    Returns:
        The validated value

    Raises:
        TypeError: If value is not of the expected type
    """
    if not isinstance(value, expected_type):
        msg = f"{name} must be of type {expected_type.__name__}, got {type(value).__name__}"
        logger.error(msg)
        raise TypeError(msg)
    return value


def validate_not_none(value: Optional[T], name: str = "value") -> T:
    """Validate that a value is not None.

    Args:
        value: Value to validate
        name: Name of the value for error messages

    Returns:
        The validated value

    Raises:
        ValueError: If value is None
    """
    if value is None:
        msg = f"{name} cannot be None"
        logger.error(msg)
        raise ValueError(msg)
    return value


def validate_path(
    path: Union[str, Path],
    should_exist: bool = True,
    should_be_file: bool = True,
    name: str = "path"
) -> Path:
    """Validate a file or directory path.

    Args:
        path: Path to validate
        should_exist: Whether the path should exist
        should_be_file: Whether the path should be a file (if False, should be directory)
        name: Name of the path for error messages

    Returns:
        Validated Path object

    Raises:
        ValueError: If path validation fails
    """
    path = Path(path)

    if should_exist and not path.exists():
        msg = f"{name} does not exist: {path}"
        logger.error(msg)
        raise ValueError(msg)

    if should_exist:
        if should_be_file and not path.is_file():
            msg = f"{name} is not a file: {path}"
            logger.error(msg)
            raise ValueError(msg)
        if not should_be_file and not path.is_dir():
            msg = f"{name} is not a directory: {path}"
            logger.error(msg)
            raise ValueError(msg)

    return path


def validate_url(url: str, pattern: Optional[Pattern] = None, name: str = "URL") -> str:
    """Validate a URL string.

    Args:
        url: URL to validate
        pattern: Optional regex pattern for specific URL format
        name: Name of the URL for error messages

    Returns:
        The validated URL

    Raises:
        ValueError: If URL validation fails
    """
    # Basic URL validation
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValueError
    except ValueError:
        msg = f"Invalid {name}: {url}"
        logger.error(msg)
        raise ValueError(msg)

    # Pattern matching if provided
    if pattern and not pattern.match(url):
        msg = f"{name} does not match expected format: {url}"
        logger.error(msg)
        raise ValueError(msg)

    return url


def validate_github_url(url: str) -> str:
    """Validate a GitHub repository URL.

    Args:
        url: GitHub URL to validate

    Returns:
        The validated GitHub URL

    Raises:
        ValueError: If URL validation fails
    """
    return validate_url(url, GITHUB_URL_PATTERN, "GitHub URL")


def validate_email(email: str) -> str:
    """Validate an email address.

    Args:
        email: Email address to validate

    Returns:
        The validated email address

    Raises:
        ValueError: If email validation fails
    """
    if not EMAIL_PATTERN.match(email):
        msg = f"Invalid email address: {email}"
        logger.error(msg)
        raise ValueError(msg)
    return email


def validate_in_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    name: str = "value"
) -> Union[int, float]:
    """Validate that a numeric value is within a range.

    Args:
        value: Value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        name: Name of the value for error messages

    Returns:
        The validated value

    Raises:
        ValueError: If value is out of range
    """
    if min_value is not None and value < min_value:
        msg = f"{name} must be >= {min_value}, got {value}"
        logger.error(msg)
        raise ValueError(msg)

    if max_value is not None and value > max_value:
        msg = f"{name} must be <= {max_value}, got {value}"
        logger.error(msg)
        raise ValueError(msg)

    return value


def validate_list_not_empty(values: List[Any], name: str = "list") -> List[Any]:
    """Validate that a list is not empty.

    Args:
        values: List to validate
        name: Name of the list for error messages

    Returns:
        The validated list

    Raises:
        ValueError: If list is empty
    """
    if not values:
        msg = f"{name} cannot be empty"
        logger.error(msg)
        raise ValueError(msg)
    return values
