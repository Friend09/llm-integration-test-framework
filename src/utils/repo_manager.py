"""Module for managing Git repository operations."""
import os
import logging
from pathlib import Path
from git import Repo
from git.exc import GitCommandError

logger = logging.getLogger(__name__)

class RepoManager:
    """Class to manage Git repository operations."""

    def __init__(self, base_dir: Path) -> None:
        """Initialize the repo manager with a base directory for cloning repositories.

        Args:
            base_dir: Base directory where repositories will be cloned
        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_repo: Repo | None = None

    async def clone_repo(self, repo_url: str | Path) -> Path:
        """
        Clone a repository from the given URL and return the path.
        If the repository already exists locally, return its path.
        """
        try:
            # Convert Path objects to string for repo_url
            repo_url_str = str(repo_url) if isinstance(repo_url, Path) else repo_url

            # Extract repo name from the URL
            repo_name = repo_url_str.split("/")[-1].replace(".git", "")
            repo_path = self.base_dir / repo_name

            if repo_path.exists():
                logger.info(f"Repository {repo_name} already exists at {repo_path}")
                self.current_repo = Repo(repo_path)
                return repo_path

            logger.info(f"Cloning repository {repo_url_str} to {repo_path}")
            import asyncio
            await asyncio.to_thread(Repo.clone_from, repo_url_str, str(repo_path))
            logger.info(f"Repository {repo_name} cloned successfully")

            # Set current_repo after successful clone
            self.current_repo = Repo(repo_path)
            return repo_path
        except GitCommandError as e:
            logger.error(f"Error cloning repository: {e}")
            raise

    def get_current_repo(self) -> Repo | None:
        """Get the current repository instance.

        Returns:
            Current Repo instance or None if no repository is cloned
        """
        return self.current_repo

    async def cleanup(self) -> None:
        """Clean up repository files if needed."""
        if self.current_repo:
            try:
                repo_path = Path(self.current_repo.working_dir)
                if repo_path.exists():
                    import shutil
                    import asyncio
                    # Run cleanup in a separate thread to not block the event loop
                    await asyncio.to_thread(shutil.rmtree, repo_path)
                    logger.info(f"Cleaned up repository at {repo_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup repository: {e}")
