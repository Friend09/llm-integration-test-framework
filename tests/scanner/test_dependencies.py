"""Tests for dependency tracking functionality."""

import pytest
from pathlib import Path

from src.scanner.dependencies import ComponentInfo, DependencyGraph, DependencyInfo
from src.scanner.python_scanner import PythonScanner
from src.utils.file_utils import safe_write_file, ensure_directory


@pytest.fixture
def dependency_test_repo(tmp_path):
    """Create a test repository with dependency relationships."""
    files = {
        "models.py": """
from typing import Optional
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
""",
        "views.py": """
from flask import Blueprint, jsonify
from .models import User
from .services import get_user

bp = Blueprint("users", __name__)

@bp.route("/users/<int:user_id>")
def get_user_view(user_id: int):
    user = get_user(user_id)
    return jsonify(user.to_dict())
""",
        "services.py": """
from typing import Optional
from .models import User

def get_user(user_id: int) -> Optional[User]:
    return User.query.get(user_id)

def create_user(name: str) -> User:
    user = User(name=name)
    return user
"""
    }

    for path, content in files.items():
        full_path = tmp_path / path
        ensure_directory(full_path.parent)
        safe_write_file(full_path, content)

    return tmp_path


def test_component_creation(dependency_test_repo):
    """Test component creation in dependency graph."""
    scanner = PythonScanner(dependency_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check models.py components
    assert graph.get_component("models.User") is not None
    assert graph.get_component("models") is not None

    # Check views.py components
    assert graph.get_component("views.get_user_view") is not None
    assert graph.get_component("views") is not None

    # Check services.py components
    assert graph.get_component("services.get_user") is not None
    assert graph.get_component("services.create_user") is not None


def test_import_dependencies(dependency_test_repo):
    """Test import dependency tracking."""
    scanner = PythonScanner(dependency_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check views.py imports
    views_deps = graph.get_dependencies("views")
    assert any(
        dep.target_component == "models.User" and dep.dependency_type == "import"
        for dep in views_deps
    )
    assert any(
        dep.target_component == "services.get_user" and dep.dependency_type == "import"
        for dep in views_deps
    )


def test_inheritance_dependencies(dependency_test_repo):
    """Test inheritance dependency tracking."""
    scanner = PythonScanner(dependency_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check User class inheritance
    user_deps = graph.get_dependencies("models.User")
    assert any(
        dep.target_component == "Base" and dep.dependency_type == "inherits"
        for dep in user_deps
    )


def test_integration_point_detection(dependency_test_repo):
    """Test integration point detection."""
    scanner = PythonScanner(dependency_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check route handler
    user_view = graph.get_component("views.get_user_view")
    assert user_view is not None
    assert user_view.is_integration_point
    assert user_view.framework_type == "flask"


def test_framework_component_detection(dependency_test_repo):
    """Test framework component detection."""
    scanner = PythonScanner(dependency_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Get all Flask components
    flask_components = graph.get_framework_components("flask")
    assert len(flask_components) > 0
    assert any(comp.name == "views.get_user_view" for comp in flask_components)


def test_cyclic_dependency_detection(dependency_test_repo):
    """Test cyclic dependency detection."""
    # Add a cyclic dependency
    service_file = dependency_test_repo / "services.py"
    with open(service_file, "a") as f:
        f.write("""
from .views import bp

def init_views():
    return bp
""")

    scanner = PythonScanner(dependency_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    cycles = graph.find_cycles()
    assert len(cycles) > 0  # Should detect the views <-> services cycle


def test_critical_component_detection(dependency_test_repo):
    """Test critical component detection."""
    scanner = PythonScanner(dependency_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # User model should be critical (used by both views and services)
    critical = graph.get_critical_components(threshold=3)
    assert any(comp.name == "models.User" for comp in critical)


def test_component_complexity(dependency_test_repo):
    """Test component complexity calculation."""
    scanner = PythonScanner(dependency_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    # Check User model complexity
    user_complexity = graph.calculate_complexity("models.User")
    assert user_complexity > 1  # Should have dependencies and dependents


def test_graph_serialization(dependency_test_repo):
    """Test dependency graph serialization."""
    scanner = PythonScanner(dependency_test_repo)
    scanner.scan()
    graph = scanner.dependency_graph

    data = graph.to_dict()
    assert "components" in data
    assert any("models.User" in comp for comp in data["components"])
    assert any("views.get_user_view" in comp for comp in data["components"])
