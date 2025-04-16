"""Repository manager for handling Git repositories."""

import os
import tempfile
from contextlib import contextmanager
import git

class RepositoryManager:
    """Manages Git repository operations."""

    def __init__(self, repo_url: str):
        """Initialize with repository URL."""
        self.repo_url = repo_url
        self.repo_path = None
        self.repo = None

    @contextmanager
    def __enter__(self):
        """Clone repository and provide path."""
        self.repo_path = tempfile.mkdtemp()
        try:
            self.repo = git.Repo.clone_from(self.repo_url, self.repo_path)
            yield self.repo_path
        finally:
            if self.repo:
                self.repo.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up repository."""
        if self.repo_path and os.path.exists(self.repo_path):
            import shutil
            shutil.rmtree(self.repo_path)
