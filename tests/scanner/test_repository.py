"""Tests for repository management functionality."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import git
import pytest
from git.exc import GitCommandError

from src.scanner.repository import RepositoryManager
from src.utils.file_utils import safe_write_file


def test_repository_initialization():
    """Test repository manager initialization."""
    url = "https://github.com/user/repo"
    manager = RepositoryManager(url)
    assert manager.repo_url == url
    assert manager.branch is None
    assert manager.auth_token is None
    assert manager.work_dir is None


def test_invalid_repository_url():
    """Test initialization with invalid URL."""
    with pytest.raises(ValueError):
        RepositoryManager("not-a-url")


def test_clone_url_with_token():
    """Test clone URL generation with auth token."""
    url = "https://github.com/user/repo"
    token = "test-token"
    manager = RepositoryManager(url, auth_token=token)
    assert manager.clone_url == f"https://{token}@github.com/user/repo"


def test_repo_name_extraction():
    """Test repository name extraction from URL."""
    cases = [
        ("https://github.com/user/repo", "repo"),
        ("https://github.com/user/repo/", "repo"),
        ("https://github.com/org/project.git", "project.git"),
    ]

    for url, expected in cases:
        manager = RepositoryManager(url)
        assert manager.repo_name == expected


@patch("git.Repo")
def test_clone_repository(mock_repo, tmp_path):
    """Test repository cloning."""
    url = "https://github.com/user/repo"
    manager = RepositoryManager(url)

    # Mock the clone operation
    mock_repo.clone_from.return_value = MagicMock()

    with manager.clone() as repo_path:
        assert repo_path.exists()
        mock_repo.clone_from.assert_called_once_with(url, repo_path)


@patch("git.Repo")
def test_clone_with_branch(mock_repo, tmp_path):
    """Test repository cloning with specific branch."""
    url = "https://github.com/user/repo"
    branch = "develop"
    manager = RepositoryManager(url, branch=branch)

    # Mock the clone and checkout operations
    mock_repo_instance = MagicMock()
    mock_repo.clone_from.return_value = mock_repo_instance

    with manager.clone():
        mock_repo_instance.git.checkout.assert_called_once_with(branch)


@patch("git.Repo")
def test_clone_error_handling(mock_repo, tmp_path):
    """Test error handling during clone."""
    url = "https://github.com/user/repo"
    manager = RepositoryManager(url)

    # Mock clone failure
    mock_repo.clone_from.side_effect = GitCommandError("clone", "error")

    with pytest.raises(GitCommandError):
        with manager.clone():
            pass


@patch("git.Repo")
def test_metadata_extraction(mock_repo):
    """Test repository metadata extraction."""
    url = "https://github.com/user/repo"
    manager = RepositoryManager(url)

    # Mock repository and commit data
    mock_repo_instance = MagicMock()
    mock_commit = MagicMock()
    mock_commit.hexsha = "abc123"
    mock_commit.message = "Test commit\n"
    mock_commit.author.name = "Test User"
    mock_commit.author.email = "test@example.com"
    mock_commit.committed_datetime = "2024-01-01 00:00:00"

    mock_repo_instance.head.commit = mock_commit
    mock_repo_instance.active_branch.name = "main"
    manager._repo = mock_repo_instance

    metadata = manager.get_metadata()
    assert metadata["name"] == "repo"
    assert metadata["default_branch"] == "main"
    assert metadata["head_commit"] == "abc123"
    assert metadata["author"] == "Test User <test@example.com>"


def test_metadata_without_clone():
    """Test metadata extraction without cloned repository."""
    manager = RepositoryManager("https://github.com/user/repo")
    with pytest.raises(RuntimeError):
        manager.get_metadata()


def test_work_dir_persistence(tmp_path):
    """Test repository persistence with work_dir."""
    url = "https://github.com/user/repo"
    manager = RepositoryManager(url, work_dir=tmp_path)

    expected_path = tmp_path / "repo"

    # Create a dummy repository
    with manager.clone() as repo_path:
        assert repo_path == expected_path
        safe_write_file(repo_path / "test.txt", "test")

    # Directory should still exist after context exit
    assert expected_path.exists()
    assert (expected_path / "test.txt").exists()


def test_is_git_repo(tmp_path):
    """Test Git repository detection."""
    url = "https://github.com/user/repo"
    manager = RepositoryManager(url)

    # Not a Git repository
    assert not manager.is_git_repo(tmp_path)

    # Create a mock Git repository
    git.Repo.init(tmp_path)
    assert manager.is_git_repo(tmp_path)


def test_repository_validation():
    """Test repository URL validation."""
    # Valid URLs
    RepositoryManager("https://github.com/user/repo.git")
    RepositoryManager("https://github.com/user/repo")

    # Invalid URLs
    with pytest.raises(ValueError):
        RepositoryManager("not_a_url")
    with pytest.raises(ValueError):
        RepositoryManager("http://example.com/not_git")
    with pytest.raises(ValueError):
        RepositoryManager("file:///local/path")


def test_target_directory_handling(tmp_path):
    """Test handling of target directory specification."""
    # With specified directory
    target_dir = tmp_path / "repo"
    manager = RepositoryManager("https://github.com/user/repo.git", target_dir=target_dir)
    assert manager.target_dir == target_dir

    # Without specified directory (should create temp dir)
    manager = RepositoryManager("https://github.com/user/repo.git")
    assert manager.target_dir.exists()
    assert "llm_test_framework_" in str(manager.target_dir)

    # Cleanup should remove temp directory
    temp_path = manager.target_dir
    manager.cleanup()
    assert not temp_path.exists()


def test_context_manager(tmp_path):
    """Test context manager functionality."""
    repo_url = "https://github.com/user/repo.git"

    # Mock git.Repo.clone_from to avoid actual cloning
    class MockRepo:
        class MockBranch:
            name = "main"
        class MockCommit:
            hexsha = "abc123"
        active_branch = MockBranch()
        head = type('Head', (), {'commit': MockCommit()})

    import git
    original_clone = git.Repo.clone_from
    git.Repo.clone_from = lambda *args, **kwargs: MockRepo()

    try:
        with RepositoryManager(repo_url) as repo_path:
            assert repo_path.exists()
            assert "llm_test_framework_" in str(repo_path)
        # Directory should be cleaned up after context exit
        assert not repo_path.exists()
    finally:
        git.Repo.clone_from = original_clone


def test_repository_info():
    """Test repository information retrieval."""
    # Mock git.Repo.clone_from to avoid actual cloning
    class MockRepo:
        class MockBranch:
            name = "main"
        class MockCommit:
            hexsha = "abc123"
        active_branch = MockBranch()
        head = type('Head', (), {'commit': MockCommit()})

    import git
    original_clone = git.Repo.clone_from
    git.Repo.clone_from = lambda *args, **kwargs: MockRepo()

    try:
        manager = RepositoryManager("https://github.com/user/repo.git")
        manager.clone()

        assert manager.get_default_branch() == "main"
        assert manager.get_latest_commit() == "abc123"

        # Test accessing info before cloning
        manager = RepositoryManager("https://github.com/user/repo.git")
        with pytest.raises(ValueError):
            manager.get_default_branch()
        with pytest.raises(ValueError):
            manager.get_latest_commit()
    finally:
        git.Repo.clone_from = original_clone
