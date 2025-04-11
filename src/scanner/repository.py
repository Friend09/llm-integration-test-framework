"""Repository management functionality for cloning and handling Git repositories."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

import git
from git.exc import GitCommandError, InvalidGitRepositoryError

from src.utils.validation_utils import validate_url, validate_path


class RepositoryManager:
    """Manages Git repository operations including cloning and cleanup."""

    def __init__(self, repo_url: str, target_dir: Optional[Union[str, Path]] = None):
        """Initialize repository manager.

        Args:
            repo_url: URL of the Git repository
            target_dir: Optional directory to clone into. If None, uses temporary directory
        """
        self.repo_url = validate_url(repo_url, "Repository URL")
        self._validate_git_url(self.repo_url)

        if target_dir:
            self.target_dir = validate_path(target_dir, should_exist=False, name="Target directory")
        else:
            self.temp_dir = tempfile.mkdtemp(prefix="llm_test_framework_")
            self.target_dir = Path(self.temp_dir)

        self.repo: Optional[git.Repo] = None

    def _validate_git_url(self, url: str) -> None:
        """Validate that URL is a valid Git repository URL.

        Args:
            url: URL to validate

        Raises:
            ValueError: If URL is not a valid Git repository URL
        """
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid Git URL: {url}")

        if not (url.endswith(".git") or "github.com" in url):
            raise ValueError(f"URL does not appear to be a Git repository: {url}")

    def clone(self) -> Path:
        """Clone the repository to the target directory.

        Returns:
            Path to the cloned repository

        Raises:
            GitCommandError: If cloning fails
        """
        try:
            self.repo = git.Repo.clone_from(self.repo_url, self.target_dir)
            return self.target_dir
        except GitCommandError as e:
            raise GitCommandError(f"Failed to clone repository: {e.command}", e.status, e.stderr)

    def cleanup(self) -> None:
        """Clean up temporary directory if one was created."""
        if hasattr(self, 'temp_dir') and self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def get_default_branch(self) -> str:
        """Get the default branch name of the repository.

        Returns:
            Name of the default branch

        Raises:
            ValueError: If repository hasn't been cloned yet
        """
        if not self.repo:
            raise ValueError("Repository has not been cloned yet")
        return self.repo.active_branch.name

    def get_latest_commit(self) -> str:
        """Get the latest commit hash.

        Returns:
            Latest commit hash

        Raises:
            ValueError: If repository hasn't been cloned yet
        """
        if not self.repo:
            raise ValueError("Repository has not been cloned yet")
        return self.repo.head.commit.hexsha

    def __enter__(self) -> Path:
        """Context manager entry point.

        Returns:
            Path to the cloned repository
        """
        return self.clone()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point."""
        self.cleanup()
