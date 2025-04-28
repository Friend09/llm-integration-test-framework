"""Integration point detection and analysis module."""

from typing import Dict, List, Optional, Set
import ast
import re
from pathlib import Path

from ..models.integration_points.base import IntegrationPoint
from ..models.integration_points.api import APIIntegrationPoint
from ..models.integration_points.database import DatabaseIntegrationPoint
from ..models.integration_points.service import ServiceIntegrationPoint


class IntegrationPointDetector:
    """Detects and analyzes integration points in the codebase."""

    def __init__(self):
        """Initialize the integration point detector."""
        self.integration_points: List[IntegrationPoint] = []
        self._api_patterns = {
            "flask": r"@.*route\(['\"].*['\"]\)",
            "django": r"path\(['\"].*['\"]\s*,",
            "fastapi": r"@.*\.(get|post|put|delete|patch)\(['\"].*['\"]\)"
        }
        self._db_patterns = {
            "sqlalchemy": r"(create_engine|Session|relationship)\(",
            "django_orm": r"models\.(Model|Manager|Field)",
            "raw_sql": r"execute\(['\"].*SELECT|INSERT|UPDATE|DELETE.*['\"]\)"
        }
        self._service_patterns = {
            "http": r"(requests|httpx)\.(get|post|put|delete|patch)\(",
            "grpc": r"grpc\.(insecure_)?channel\(",
            "websocket": r"websockets\.(connect|WebSocket)\("
        }

    def detect_integration_points(self, file_path: Path, content: str) -> List[IntegrationPoint]:
        """Detect integration points in a given file."""
        points: List[IntegrationPoint] = []

        # Parse Python file
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Log error and skip file if it can't be parsed
            return points

        # Detect API endpoints
        api_points = self._detect_api_endpoints(file_path, tree, content)
        points.extend(api_points)

        # Detect database operations
        db_points = self._detect_database_operations(file_path, tree, content)
        points.extend(db_points)

        # Detect service communications
        service_points = self._detect_service_communications(file_path, tree, content)
        points.extend(service_points)

        return points

    def _detect_api_endpoints(self, file_path: Path, tree: ast.AST, content: str) -> List[APIIntegrationPoint]:
        """Detect API endpoints in the code."""
        endpoints: List[APIIntegrationPoint] = []

        for node in ast.walk(tree):
            # Look for route decorators
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    endpoint = self._analyze_route_decorator(decorator, node, file_path)
                    if endpoint:
                        endpoints.append(endpoint)

        return endpoints

    def _analyze_route_decorator(self, decorator: ast.AST, func_node: ast.FunctionDef, file_path: Path) -> Optional[APIIntegrationPoint]:
        """Analyze a route decorator to extract API endpoint information."""
        route_pattern = ""
        http_method = "GET"
        auth_required = False

        # Extract route pattern and HTTP method
        if isinstance(decorator, ast.Call):
            if hasattr(decorator.func, "attr") and decorator.func.attr in ["route", "get", "post", "put", "delete", "patch"]:
                if decorator.args:
                    route_pattern = self._extract_string_value(decorator.args[0])
                if decorator.func.attr != "route":
                    http_method = decorator.func.attr.upper()

        if not route_pattern:
            return None

        # Check for authentication requirements
        auth_required = self._check_auth_requirements(func_node)

        # Create API integration point
        return APIIntegrationPoint(
            name=f"{http_method} {route_pattern}",
            location=str(file_path),
            integration_type="api",
            source_component=file_path.stem,
            target_component="client",
            http_method=http_method,
            route_pattern=route_pattern,
            auth_required=auth_required
        )

    def _detect_database_operations(self, file_path: Path, tree: ast.AST, content: str) -> List[DatabaseIntegrationPoint]:
        """Detect database operations in the code."""
        operations: List[DatabaseIntegrationPoint] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                db_op = self._analyze_database_call(node, file_path)
                if db_op:
                    operations.append(db_op)

        return operations

    def _analyze_database_call(self, node: ast.Call, file_path: Path) -> Optional[DatabaseIntegrationPoint]:
        """Analyze a potential database operation call."""
        if not hasattr(node.func, "attr"):
            return None

        operation_type = "read"
        uses_orm = False
        uses_transactions = False

        # Detect SQLAlchemy operations
        if hasattr(node.func, "value") and isinstance(node.func.value, ast.Name):
            if node.func.value.id in ["session", "db"]:
                if node.func.attr in ["query", "get", "filter"]:
                    operation_type = "read"
                elif node.func.attr in ["add", "update"]:
                    operation_type = "write"
                elif node.func.attr == "delete":
                    operation_type = "delete"
                uses_orm = True

        # Create database integration point
        if operation_type:
            return DatabaseIntegrationPoint(
                name=f"Database {operation_type}",
                location=str(file_path),
                integration_type="database",
                source_component=file_path.stem,
                target_component="database",
                operation_type=operation_type,
                uses_orm=uses_orm,
                uses_transactions=uses_transactions
            )

        return None

    def _detect_service_communications(self, file_path: Path, tree: ast.AST, content: str) -> List[ServiceIntegrationPoint]:
        """Detect service-to-service communications in the code."""
        communications: List[ServiceIntegrationPoint] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                service_comm = self._analyze_service_call(node, file_path)
                if service_comm:
                    communications.append(service_comm)

        return communications

    def _analyze_service_call(self, node: ast.Call, file_path: Path) -> Optional[ServiceIntegrationPoint]:
        """Analyze a potential service communication call."""
        if not hasattr(node.func, "attr"):
            return None

        protocol = "http"
        service_name = "unknown"
        has_timeout = False
        has_retry = False

        # Detect HTTP client calls
        if hasattr(node.func, "value") and isinstance(node.func.value, ast.Name):
            if node.func.value.id in ["requests", "httpx"]:
                if node.func.attr in ["get", "post", "put", "delete", "patch"]:
                    # Check for timeout and retry configuration in keywords
                    for keyword in node.keywords:
                        if keyword.arg == "timeout":
                            has_timeout = True
                        elif keyword.arg == "retry":
                            has_retry = True

                    # Try to extract service name from URL
                    if node.args:
                        url = self._extract_string_value(node.args[0])
                        if url:
                            service_name = self._extract_service_name(url)

        # Create service integration point
        if service_name:
            return ServiceIntegrationPoint(
                name=f"Service call to {service_name}",
                location=str(file_path),
                integration_type="service",
                source_component=file_path.stem,
                target_component=service_name,
                protocol=protocol,
                service_name=service_name,
                has_timeout=has_timeout,
                has_retry_logic=has_retry
            )

        return None

    def _extract_string_value(self, node: ast.AST) -> str:
        """Extract string value from an AST node."""
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""

    def _check_auth_requirements(self, node: ast.FunctionDef) -> bool:
        """Check if a function has authentication requirements."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id in ["login_required", "requires_auth"]:
                return True
            elif isinstance(decorator, ast.Call):
                if hasattr(decorator.func, "id") and decorator.func.id in ["login_required", "requires_auth"]:
                    return True
        return False

    def _extract_service_name(self, url: str) -> str:
        """Extract service name from a URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.split(".")[0]
        except Exception:
            return "unknown"
