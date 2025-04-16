"""Cleanup script for removing unnecessary files and folders."""
import os
import shutil
from pathlib import Path

def cleanup():
    """Remove unnecessary files and folders."""
    # Get the project root directory
    root_dir = Path(__file__).parent

    # Patterns to remove
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/*.so",
        "**/*.egg-info",
        "**/.DS_Store",
        "**/*.swp",
        "**/*.swo",
        "**/*.bak",
        "**/*.tmp"
    ]

    # Remove matching files and directories
    for pattern in patterns:
        for path in root_dir.glob(pattern):
            if path.is_file():
                path.unlink()
                print(f"Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                print(f"Removed directory: {path}")

    # Remove empty directories
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                dir_path.rmdir()
                print(f"Removed empty directory: {dir_path}")
            except OSError:
                pass  # Directory not empty

if __name__ == "__main__":
    cleanup()
