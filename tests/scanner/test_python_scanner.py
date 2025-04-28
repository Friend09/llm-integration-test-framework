"""Tests for Python scanner functionality."""

import pytest
from pathlib import Path

from src.scanner.python_scanner import PythonScanner
from src.utils.file_utils import safe_write_file, ensure_directory


@pytest.fixture
def test_repo(tmp_path):
    """Create a test repository with Python files."""
    files = {
        "simple.py": """
import os
from pathlib import Path

def hello(name: str) -> str:
    \"\"\"Say hello.\"\"\"
    return f"Hello {name}"

async def fetch_data():
    return {"data": "value"}
""",
        "classes.py": """
from typing import Optional

class BaseClass:
    \"\"\"Base class docstring.\"\"\"
    def __init__(self):
        pass

class ChildClass(BaseClass):
    @property
    def name(self) -> str:
        return "child"

    async def process(self) -> None:
        await self.fetch_data()
""",
        "flask_app.py": """
from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello World"

@app.route("/api", methods=["POST"])
async def api():
    data = await request.get_json()
    return data
""",
        "django_views.py": """
from django.views import View
from django.http import HttpResponse

class HomeView(View):
    def get(self, request):
        return HttpResponse("Home")

    def post(self, request):
        return HttpResponse("Posted")
""",
        "fastapi_app.py": """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/items")
def create_item(item: dict):
    return item
"""
    }

    for path, content in files.items():
        full_path = tmp_path / path
        ensure_directory(full_path.parent)
        safe_write_file(full_path, content)

    return tmp_path


def test_scanner_initialization(test_repo):
    """Test Python scanner initialization."""
    scanner = PythonScanner(test_repo)
    assert scanner.root_path == test_repo
    assert scanner.include_patterns == ["**/*.py"]
    assert len(scanner.scanned_files) == 0


def test_import_detection(test_repo):
    """Test import statement detection."""
    scanner = PythonScanner(test_repo)
    scanner.scan()

    # Check simple.py imports
    simple_imports = scanner.imports[test_repo / "simple.py"]
    assert len(simple_imports) == 2
    assert any(imp.module_name == "os" for imp in simple_imports)
    assert any(imp.module_name == "pathlib" and "Path" in imp.imported_names for imp in simple_imports)


def test_function_detection(test_repo):
    """Test function detection."""
    scanner = PythonScanner(test_repo)
    scanner.scan()

    # Check simple.py functions
    simple_funcs = scanner.functions[test_repo / "simple.py"]
    assert len(simple_funcs) == 2

    hello_func = next(f for f in simple_funcs if f.name == "hello")
    assert hello_func.args == ["name"]
    assert not hello_func.is_async
    assert hello_func.docstring is not None

    fetch_func = next(f for f in simple_funcs if f.name == "fetch_data")
    assert fetch_func.is_async
    assert len(fetch_func.args) == 0


def test_class_detection(test_repo):
    """Test class detection."""
    scanner = PythonScanner(test_repo)
    scanner.scan()

    # Check classes.py
    classes = scanner.classes[test_repo / "classes.py"]
    assert len(classes) == 2

    base_class = next(c for c in classes if c.name == "BaseClass")
    assert len(base_class.bases) == 0
    assert base_class.docstring is not None
    assert "__init__" in base_class.methods

    child_class = next(c for c in classes if c.name == "ChildClass")
    assert "BaseClass" in child_class.bases
    assert len(child_class.methods) == 2
    assert child_class.methods["process"].is_async


def test_flask_detection(test_repo):
    """Test Flask pattern detection."""
    scanner = PythonScanner(test_repo)
    scanner.scan()

    # Check flask_app.py
    flask_info = scanner.framework_info[test_repo / "flask_app.py"]["flask"]
    assert len(flask_info) == 2

    index_route = next(r for r in flask_info if r["function"] == "index")
    assert r["type"] == "route"
    assert not r["is_async"]

    api_route = next(r for r in flask_info if r["function"] == "api")
    assert r["type"] == "route"
    assert r["is_async"]


def test_django_detection(test_repo):
    """Test Django pattern detection."""
    scanner = PythonScanner(test_repo)
    scanner.scan()

    # Check django_views.py
    django_info = scanner.framework_info[test_repo / "django_views.py"]["django"]
    assert len(django_info) == 1

    view_info = django_info[0]
    assert view_info["type"] == "view"
    assert view_info["class"] == "HomeView"
    assert "get" in view_info["methods"]
    assert "post" in view_info["methods"]


def test_fastapi_detection(test_repo):
    """Test FastAPI pattern detection."""
    scanner = PythonScanner(test_repo)
    scanner.scan()

    # Check fastapi_app.py
    fastapi_info = scanner.framework_info[test_repo / "fastapi_app.py"]["fastapi"]
    assert len(fastapi_info) == 2

    root_endpoint = next(e for e in fastapi_info if e["function"] == "root")
    assert e["type"] == "endpoint"
    assert e["is_async"]

    items_endpoint = next(e for e in fastapi_info if e["function"] == "create_item")
    assert e["type"] == "endpoint"
    assert not e["is_async"]


def test_error_handling(test_repo):
    """Test error handling for invalid Python files."""
    # Create file with syntax error
    invalid_file = test_repo / "invalid.py"
    safe_write_file(invalid_file, "def invalid_syntax(:")

    scanner = PythonScanner(test_repo)
    scanner.scan()

    assert invalid_file in scanner.get_errors()
    assert "invalid syntax" in scanner.get_errors()[invalid_file].lower()
