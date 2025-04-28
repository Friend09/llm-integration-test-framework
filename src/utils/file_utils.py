"""File utilities for safe file operations."""

import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional, Union

from src.utils.logging import logger


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists

    Returns:
        Path object for the directory

    Raises:
        OSError: If directory creation fails
    """
    path = Path(path)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except OSError as e:
        logger.error(f"Failed to create directory {path}", extra={"error": str(e)})
        raise


def safe_read_file(path: Union[str, Path], encoding: str = "utf-8") -> str:
    """Safely read a file with proper error handling.

    Args:
        path: Path to the file to read
        encoding: File encoding (default: utf-8)

    Returns:
        Contents of the file as a string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file reading fails
    """
    path = Path(path)
    try:
        with path.open("r", encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise
    except IOError as e:
        logger.error(f"Failed to read file {path}", extra={"error": str(e)})
        raise


def safe_write_file(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    make_parents: bool = True
) -> None:
    """Safely write content to a file with proper error handling.

    Args:
        path: Path to write the file to
        content: Content to write
        encoding: File encoding (default: utf-8)
        make_parents: Create parent directories if they don't exist

    Raises:
        IOError: If file writing fails
    """
    path = Path(path)
    if make_parents:
        ensure_directory(path.parent)

    try:
        with path.open("w", encoding=encoding) as f:
            f.write(content)
    except IOError as e:
        logger.error(f"Failed to write file {path}", extra={"error": str(e)})
        raise


def safe_delete_file(path: Union[str, Path]) -> None:
    """Safely delete a file with proper error handling.

    Args:
        path: Path to the file to delete

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file deletion fails
    """
    path = Path(path)
    try:
        path.unlink()
    except FileNotFoundError:
        logger.warning(f"File not found for deletion: {path}")
        raise
    except IOError as e:
        logger.error(f"Failed to delete file {path}", extra={"error": str(e)})
        raise


def filter_files(
    directory: Union[str, Path],
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_size: Optional[int] = None
) -> List[Path]:
    """Filter files in a directory based on patterns and size.

    Args:
        directory: Directory to search in
        include_patterns: List of glob patterns to include
        exclude_patterns: List of glob patterns to exclude
        max_size: Maximum file size in bytes

    Returns:
        List of Path objects for matching files
    """
    directory = Path(directory)
    include_patterns = include_patterns or ["*"]
    exclude_patterns = exclude_patterns or []

    # First, get all files matching include patterns
    matching_files = set()
    for pattern in include_patterns:
        matching_files.update(directory.rglob(pattern))

    # Remove files matching exclude patterns
    for pattern in exclude_patterns:
        exclude_files = set(directory.rglob(pattern))
        matching_files -= exclude_files

    # Filter by size if specified
    if max_size is not None:
        matching_files = {f for f in matching_files if f.is_file() and f.stat().st_size <= max_size}

    return sorted(matching_files)


@contextmanager
def temp_directory(prefix: str = "temp_") -> Generator[Path, None, None]:
    """Create a temporary directory and clean it up when done.

    Args:
        prefix: Prefix for the temporary directory name

    Yields:
        Path object for the temporary directory
    """
    temp_dir = Path(os.getcwd()) / f"{prefix}{os.urandom(4).hex()}"
    try:
        ensure_directory(temp_dir)
        yield temp_dir
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary directory {temp_dir}", extra={"error": str(e)})


def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize a file path.

    Args:
        path: Path to normalize

    Returns:
        Normalized Path object
    """
    return Path(path).resolve().absolute()


def get_file_hash(path: Union[str, Path], algorithm: str = "sha256") -> str:
    """Calculate the hash of a file.

    Args:
        path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hex digest of the file hash

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file reading fails
    """
    import hashlib

    path = Path(path)
    hash_obj = getattr(hashlib, algorithm)()

    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise
    except IOError as e:
        logger.error(f"Failed to read file {path}", extra={"error": str(e)})
        raise
