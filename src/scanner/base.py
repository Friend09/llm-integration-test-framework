"""Base classes for repository scanning functionality."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Generator, List, Optional, Set, Union

from src.utils.file_utils import filter_files
from src.utils.logging import logger
from src.utils.validation_utils import validate_path


class BaseScanner(ABC):
    """Abstract base class for repository scanners."""

    def __init__(
        self,
        root_path: Union[str, Path],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_file_size: Optional[int] = 1024 * 1024  # 1MB default
    ):
        """Initialize the scanner.

        Args:
            root_path: Root directory to scan
            include_patterns: List of glob patterns for files to include
            exclude_patterns: List of glob patterns for files to exclude
            max_file_size: Maximum file size in bytes to process
        """
        self.root_path = validate_path(root_path, should_exist=True, should_be_file=False)
        self.include_patterns = include_patterns or self._default_include_patterns()
        self.exclude_patterns = exclude_patterns or self._default_exclude_patterns()
        self.max_file_size = max_file_size
        self._scanned_files: Set[Path] = set()
        self._errors: Dict[Path, str] = {}

    @abstractmethod
    def _default_include_patterns(self) -> List[str]:
        """Return default glob patterns for files to include.

        Returns:
            List of glob patterns
        """
        pass

    @abstractmethod
    def _default_exclude_patterns(self) -> List[str]:
        """Return default glob patterns for files to exclude.

        Returns:
            List of glob patterns
        """
        return [
            "**/__pycache__/**",
            "**/*.pyc",
            "**/.git/**",
            "**/node_modules/**",
            "**/venv/**",
            "**/.env/**",
            "**/bin/**",
            "**/obj/**",
        ]

    def get_files(self) -> Generator[Path, None, None]:
        """Get all files matching the include/exclude patterns.

        Yields:
            Path objects for matching files
        """
        files = filter_files(
            self.root_path,
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns,
            max_size=self.max_file_size
        )
        for file in files:
            if file not in self._scanned_files:
                yield file

    @abstractmethod
    def scan_file(self, file_path: Path) -> None:
        """Scan a single file and extract relevant information.

        Args:
            file_path: Path to the file to scan

        This method should be implemented by subclasses to perform
        language-specific scanning and information extraction.
        """
        pass

    def scan(self) -> None:
        """Scan all matching files in the repository."""
        logger.info(f"Starting scan of {self.root_path}")

        for file in self.get_files():
            try:
                self.scan_file(file)
                self._scanned_files.add(file)
            except Exception as e:
                logger.error(f"Error scanning {file}: {str(e)}")
                self._errors[file] = str(e)

        logger.info(
            f"Scan completed. Processed {len(self._scanned_files)} files. "
            f"Encountered {len(self._errors)} errors."
        )

    def get_errors(self) -> Dict[Path, str]:
        """Get any errors encountered during scanning.

        Returns:
            Dictionary mapping file paths to error messages
        """
        return self._errors.copy()

    @property
    def scanned_files(self) -> Set[Path]:
        """Get the set of successfully scanned files.

        Returns:
            Set of Path objects for scanned files
        """
        return self._scanned_files.copy()
