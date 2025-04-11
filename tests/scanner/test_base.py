"""Tests for the base scanner functionality."""

import pytest
from pathlib import Path
from typing import List

from src.scanner.base import BaseScanner
from src.utils.file_utils import safe_write_file, ensure_directory


class TestScanner(BaseScanner):
    """Test implementation of BaseScanner."""

    def _default_include_patterns(self) -> List[str]:
        return ["*.txt"]

    def scan_file(self, file_path: Path) -> None:
        # Simple implementation that just reads the file
        with open(file_path, "r") as f:
            f.read()


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository structure."""
    # Create some test files
    files = {
        "file1.txt": "content1",
        "file2.txt": "content2",
        "ignored.py": "python code",
        "subdir/file3.txt": "content3",
        "subdir/ignored.pyc": "compiled python",
    }

    for path, content in files.items():
        full_path = tmp_path / path
        ensure_directory(full_path.parent)
        safe_write_file(full_path, content)

    return tmp_path


def test_scanner_initialization(test_repo):
    """Test scanner initialization."""
    scanner = TestScanner(test_repo)
    assert scanner.root_path == test_repo
    assert scanner.include_patterns == ["*.txt"]
    assert "**/__pycache__/**" in scanner.exclude_patterns
    assert len(scanner.scanned_files) == 0
    assert len(scanner.get_errors()) == 0


def test_get_files(test_repo):
    """Test file filtering."""
    scanner = TestScanner(test_repo)
    files = list(scanner.get_files())

    # Should find all .txt files
    assert len(files) == 3
    assert all(f.suffix == ".txt" for f in files)

    # Should include files in subdirectories
    assert any(f.name == "file3.txt" for f in files)


def test_scan(test_repo):
    """Test scanning functionality."""
    scanner = TestScanner(test_repo)
    scanner.scan()

    # Should have scanned all .txt files
    assert len(scanner.scanned_files) == 3
    assert all(f.suffix == ".txt" for f in scanner.scanned_files)

    # Should have no errors
    assert len(scanner.get_errors()) == 0


def test_scan_with_error(test_repo):
    """Test error handling during scan."""
    class ErrorScanner(TestScanner):
        def scan_file(self, file_path: Path) -> None:
            raise ValueError("Test error")

    scanner = ErrorScanner(test_repo)
    scanner.scan()

    # Should have recorded errors for all files
    assert len(scanner.get_errors()) == 3
    assert all(isinstance(err, str) for err in scanner.get_errors().values())
    assert len(scanner.scanned_files) == 0


def test_custom_patterns(test_repo):
    """Test scanner with custom include/exclude patterns."""
    scanner = TestScanner(
        test_repo,
        include_patterns=["*.py"],
        exclude_patterns=["**/*.pyc"]
    )

    files = list(scanner.get_files())
    assert len(files) == 1
    assert files[0].name == "ignored.py"


def test_max_file_size(test_repo):
    """Test max file size filtering."""
    # Create a large file
    large_file = test_repo / "large.txt"
    safe_write_file(large_file, "x" * 2000)  # 2KB file

    scanner = TestScanner(test_repo, max_file_size=1000)  # 1KB limit
    files = list(scanner.get_files())

    # Large file should be excluded
    assert large_file not in files
