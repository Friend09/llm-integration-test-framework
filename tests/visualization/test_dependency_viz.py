"""Tests for dependency visualization functionality."""

import os
from pathlib import Path

import pytest

from src.scanner.python_scanner import PythonScanner
from src.visualization.dependency_viz import DependencyVisualizer
from src.utils.file_utils import safe_write_file, ensure_directory


@pytest.fixture
def viz_test_repo(tmp_path):
    """Create a test repository with various dependencies."""
    files = {
        "app.py": """
from flask import Flask
from .views import bp
from .models import db

app = Flask(__name__)
app.register_blueprint(bp)
db.init_app(app)
""",
        "views.py": """
from flask import Blueprint, jsonify
from .models import User
from .services import get_user, create_user

bp = Blueprint("users", __name__)

@bp.route("/users")
def list_users():
    return jsonify([u.to_dict() for u in User.query.all()])

@bp.route("/users/<int:user_id>")
def get_user_view(user_id: int):
    return jsonify(get_user(user_id).to_dict())

@bp.route("/users", methods=["POST"])
def create_user_view():
    return jsonify(create_user().to_dict())
""",
        "models.py": """
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String, unique=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }
""",
        "services.py": """
from typing import Optional
from .models import User, db

def get_user(user_id: int) -> Optional[User]:
    return User.query.get(user_id)

def create_user(name: str = "test") -> User:
    user = User(name=name)
    db.session.add(user)
    db.session.commit()
    return user
"""
    }

    for path, content in files.items():
        full_path = tmp_path / path
        ensure_directory(full_path.parent)
        safe_write_file(full_path, content)

    return tmp_path


def test_component_graph_creation(viz_test_repo, tmp_path):
    """Test creation of component dependency graph."""
    # Scan the repository
    scanner = PythonScanner(viz_test_repo)
    scanner.scan()

    # Create visualizer
    output_dir = tmp_path / "viz"
    ensure_directory(output_dir)
    visualizer = DependencyVisualizer(scanner.dependency_graph, output_dir)

    # Generate component graph
    output_file = visualizer.create_component_graph()
    assert Path(output_file).exists()
    assert output_file.endswith(".svg")


def test_module_graph_creation(viz_test_repo, tmp_path):
    """Test creation of module dependency graph."""
    scanner = PythonScanner(viz_test_repo)
    scanner.scan()

    output_dir = tmp_path / "viz"
    ensure_directory(output_dir)
    visualizer = DependencyVisualizer(scanner.dependency_graph, output_dir)

    output_file = visualizer.create_module_graph()
    assert Path(output_file).exists()
    assert output_file.endswith(".svg")


def test_integration_graph_creation(viz_test_repo, tmp_path):
    """Test creation of integration points graph."""
    scanner = PythonScanner(viz_test_repo)
    scanner.scan()

    output_dir = tmp_path / "viz"
    ensure_directory(output_dir)
    visualizer = DependencyVisualizer(scanner.dependency_graph, output_dir)

    output_file = visualizer.create_integration_graph()
    assert Path(output_file).exists()
    assert output_file.endswith(".svg")


def test_graph_customization(viz_test_repo, tmp_path):
    """Test graph customization options."""
    scanner = PythonScanner(viz_test_repo)
    scanner.scan()

    output_dir = tmp_path / "viz"
    ensure_directory(output_dir)
    visualizer = DependencyVisualizer(scanner.dependency_graph, output_dir)

    # Test different combinations of options
    variants = [
        {"include_frameworks": True, "show_integration_points": True, "group_by_module": True},
        {"include_frameworks": False, "show_integration_points": True, "group_by_module": True},
        {"include_frameworks": True, "show_integration_points": False, "group_by_module": True},
        {"include_frameworks": True, "show_integration_points": True, "group_by_module": False},
    ]

    for i, options in enumerate(variants):
        output_file = visualizer.create_component_graph(**options)
        assert Path(output_file).exists()


def test_multiple_visualizations(viz_test_repo, tmp_path):
    """Test creating multiple visualizations with different names."""
    scanner = PythonScanner(viz_test_repo)
    scanner.scan()

    output_dir = tmp_path / "viz"
    ensure_directory(output_dir)

    # Create visualizations with different names
    names = ["overview", "detailed", "summary"]
    for name in names:
        visualizer = DependencyVisualizer(
            scanner.dependency_graph,
            output_dir,
            name=name
        )
        output_file = visualizer.create_component_graph()
        assert Path(output_file).exists()
        assert name in output_file


def test_framework_detection_in_visualization(viz_test_repo, tmp_path):
    """Test that framework components are properly highlighted."""
    scanner = PythonScanner(viz_test_repo)
    scanner.scan()

    output_dir = tmp_path / "viz"
    ensure_directory(output_dir)
    visualizer = DependencyVisualizer(scanner.dependency_graph, output_dir)

    # Generate graph with framework information
    output_file = visualizer.create_component_graph(include_frameworks=True)

    # Read the generated SVG
    with open(output_file, "r") as f:
        content = f.read()

    # Check for framework-specific elements
    assert "flask" in content.lower()
    assert "#FF6B6B" in content  # Flask color


def test_integration_point_highlighting(viz_test_repo, tmp_path):
    """Test that integration points are properly highlighted."""
    scanner = PythonScanner(viz_test_repo)
    scanner.scan()

    output_dir = tmp_path / "viz"
    ensure_directory(output_dir)
    visualizer = DependencyVisualizer(scanner.dependency_graph, output_dir)

    # Generate graph with integration points highlighted
    output_file = visualizer.create_integration_graph()

    # Read the generated SVG
    with open(output_file, "r") as f:
        content = f.read()

    # Check for route handlers
    assert "list_users" in content
    assert "get_user_view" in content
    assert "create_user_view" in content
