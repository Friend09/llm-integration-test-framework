"""Python code scanner implementation."""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Type, Union

from src.scanner.base import BaseScanner
from src.scanner.dependencies import ComponentInfo, DependencyGraph, DependencyInfo
from src.utils.logging import logger


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module_name: str
    imported_names: Set[str] = field(default_factory=set)
    is_from_import: bool = False
    alias: Optional[str] = None
    line_number: int = 0


@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    args: List[str]
    decorators: List[str]
    is_async: bool = False
    is_method: bool = False
    line_number: int = 0
    docstring: Optional[str] = None


@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    bases: List[str]
    decorators: List[str]
    methods: Dict[str, FunctionInfo] = field(default_factory=dict)
    line_number: int = 0
    docstring: Optional[str] = None


class PythonScanner(BaseScanner):
    """Scanner for Python source code files."""

    def __init__(self, *args, **kwargs):
        """Initialize the Python scanner."""
        super().__init__(*args, **kwargs)
        self._imports: Dict[Path, List[ImportInfo]] = {}
        self._functions: Dict[Path, List[FunctionInfo]] = {}
        self._classes: Dict[Path, List[ClassInfo]] = {}
        self._framework_info: Dict[Path, Dict[str, List[dict]]] = {}
        self._dependency_graph = DependencyGraph()

    def _default_include_patterns(self) -> List[str]:
        """Return default glob patterns for Python files.

        Returns:
            List of glob patterns for Python files
        """
        return ["**/*.py"]

    def scan_file(self, file_path: Path) -> None:
        """Scan a Python file and extract information.

        Args:
            file_path: Path to the Python file to scan
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            visitor = PythonASTVisitor()
            visitor.visit(tree)

            # Store extracted information
            if visitor.imports:
                self._imports[file_path] = visitor.imports
            if visitor.functions:
                self._functions[file_path] = visitor.functions
            if visitor.classes:
                self._classes[file_path] = visitor.classes

            # Add components to dependency graph
            self._add_file_components(file_path, visitor)

            # Analyze framework-specific patterns
            self._analyze_frameworks(file_path, tree, visitor)

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {str(e)}")
            raise

    def _add_file_components(self, file_path: Path, visitor: "PythonASTVisitor") -> None:
        """Add file components to the dependency graph."""
        # Add module as a component
        module_name = file_path.stem
        module_component = ComponentInfo(
            name=module_name,
            file_path=file_path,
            component_type="module"
        )
        self._dependency_graph.add_component(module_component)

        # Add functions as components
        for func in visitor.functions:
            func_component = ComponentInfo(
                name=f"{module_name}.{func.name}",
                file_path=file_path,
                component_type="function",
                is_integration_point=any("route" in d for d in func.decorators)
            )
            self._dependency_graph.add_component(func_component)

            # Add dependency from module to function
            self._dependency_graph.add_dependency(DependencyInfo(
                source_file=file_path,
                source_component=module_name,
                target_file=file_path,
                target_component=func_component.name,
                dependency_type="contains",
                line_number=func.line_number
            ))

        # Add classes as components
        for cls in visitor.classes:
            cls_component = ComponentInfo(
                name=f"{module_name}.{cls.name}",
                file_path=file_path,
                component_type="class",
                is_integration_point=any(base.endswith("View") for base in cls.bases)
            )
            self._dependency_graph.add_component(cls_component)

            # Add dependency from module to class
            self._dependency_graph.add_dependency(DependencyInfo(
                source_file=file_path,
                source_component=module_name,
                target_file=file_path,
                target_component=cls_component.name,
                dependency_type="contains",
                line_number=cls.line_number
            ))

            # Add inheritance dependencies
            for base in cls.bases:
                self._dependency_graph.add_dependency(DependencyInfo(
                    source_file=file_path,
                    source_component=cls_component.name,
                    target_file=None,  # May be in another file
                    target_component=base,
                    dependency_type="inherits",
                    line_number=cls.line_number
                ))

            # Add method components
            for method_name, method in cls.methods.items():
                method_component = ComponentInfo(
                    name=f"{module_name}.{cls.name}.{method_name}",
                    file_path=file_path,
                    component_type="method",
                    is_integration_point=any("route" in d for d in method.decorators)
                )
                self._dependency_graph.add_component(method_component)

                # Add dependency from class to method
                self._dependency_graph.add_dependency(DependencyInfo(
                    source_file=file_path,
                    source_component=cls_component.name,
                    target_file=file_path,
                    target_component=method_component.name,
                    dependency_type="contains",
                    line_number=method.line_number
                ))

        # Add import dependencies
        for imp in visitor.imports:
            if imp.is_from_import:
                # From imports create dependencies to specific components
                for name in imp.imported_names:
                    self._dependency_graph.add_dependency(DependencyInfo(
                        source_file=file_path,
                        source_component=module_name,
                        target_file=None,
                        target_component=f"{imp.module_name}.{name}",
                        dependency_type="import",
                        line_number=imp.line_number
                    ))
            else:
                # Regular imports create dependencies to modules
                self._dependency_graph.add_dependency(DependencyInfo(
                    source_file=file_path,
                    source_component=module_name,
                    target_file=None,
                    target_component=imp.module_name,
                    dependency_type="import",
                    line_number=imp.line_number
                ))

    def _analyze_frameworks(
        self,
        file_path: Path,
        tree: ast.AST,
        visitor: "PythonASTVisitor"
    ) -> None:
        """Analyze framework-specific patterns in the code.

        Args:
            file_path: Path to the file being analyzed
            tree: AST of the file
            visitor: AST visitor with extracted information
        """
        framework_info = {}

        # Flask patterns
        if self._has_flask_imports(visitor.imports):
            flask_info = self._analyze_flask_patterns(tree, visitor)
            if flask_info:
                framework_info["flask"] = flask_info
                self._update_framework_components(file_path, "flask", flask_info)

        # Django patterns
        if self._has_django_imports(visitor.imports):
            django_info = self._analyze_django_patterns(tree, visitor)
            if django_info:
                framework_info["django"] = django_info
                self._update_framework_components(file_path, "django", django_info)

        # FastAPI patterns
        if self._has_fastapi_imports(visitor.imports):
            fastapi_info = self._analyze_fastapi_patterns(tree, visitor)
            if fastapi_info:
                framework_info["fastapi"] = fastapi_info
                self._update_framework_components(file_path, "fastapi", fastapi_info)

        if framework_info:
            self._framework_info[file_path] = framework_info

    def _update_framework_components(
        self,
        file_path: Path,
        framework: str,
        framework_info: List[dict]
    ) -> None:
        """Update component framework information."""
        module_name = file_path.stem

        for info in framework_info:
            component_name = None

            if info["type"] == "route" or info["type"] == "endpoint":
                component_name = f"{module_name}.{info['function']}"
            elif info["type"] == "view":
                component_name = f"{module_name}.{info['class']}"

            if component_name:
                component = self._dependency_graph.get_component(component_name)
                if component:
                    component.framework_type = framework
                    component.is_integration_point = True

    def _has_flask_imports(self, imports: List[ImportInfo]) -> bool:
        """Check if file has Flask imports."""
        return any(imp.module_name.startswith("flask") for imp in imports)

    def _has_django_imports(self, imports: List[ImportInfo]) -> bool:
        """Check if file has Django imports."""
        return any(imp.module_name.startswith("django") for imp in imports)

    def _has_fastapi_imports(self, imports: List[ImportInfo]) -> bool:
        """Check if file has FastAPI imports."""
        return any(imp.module_name.startswith("fastapi") for imp in imports)

    def _analyze_flask_patterns(
        self,
        tree: ast.AST,
        visitor: "PythonASTVisitor"
    ) -> List[dict]:
        """Analyze Flask-specific patterns.

        Args:
            tree: AST of the file
            visitor: AST visitor with extracted information

        Returns:
            List of detected Flask patterns
        """
        patterns = []

        # Look for route decorators
        for func in visitor.functions:
            route_decorators = [d for d in func.decorators if "route" in d]
            if route_decorators:
                patterns.append({
                    "type": "route",
                    "function": func.name,
                    "decorators": route_decorators,
                    "is_async": func.is_async,
                    "line": func.line_number
                })

        return patterns

    def _analyze_django_patterns(
        self,
        tree: ast.AST,
        visitor: "PythonASTVisitor"
    ) -> List[dict]:
        """Analyze Django-specific patterns.

        Args:
            tree: AST of the file
            visitor: AST visitor with extracted information

        Returns:
            List of detected Django patterns
        """
        patterns = []

        # Look for view classes
        for cls in visitor.classes:
            if any(base.endswith("View") for base in cls.bases):
                patterns.append({
                    "type": "view",
                    "class": cls.name,
                    "base_classes": cls.bases,
                    "methods": list(cls.methods.keys()),
                    "line": cls.line_number
                })

        return patterns

    def _analyze_fastapi_patterns(
        self,
        tree: ast.AST,
        visitor: "PythonASTVisitor"
    ) -> List[dict]:
        """Analyze FastAPI-specific patterns.

        Args:
            tree: AST of the file
            visitor: AST visitor with extracted information

        Returns:
            List of detected FastAPI patterns
        """
        patterns = []

        # Look for endpoint decorators
        for func in visitor.functions:
            endpoint_decorators = [
                d for d in func.decorators
                if any(method in d.lower() for method in ["get", "post", "put", "delete"])
            ]
            if endpoint_decorators:
                patterns.append({
                    "type": "endpoint",
                    "function": func.name,
                    "decorators": endpoint_decorators,
                    "is_async": func.is_async,
                    "line": func.line_number
                })

        return patterns

    @property
    def imports(self) -> Dict[Path, List[ImportInfo]]:
        """Get all discovered imports.

        Returns:
            Dictionary mapping file paths to lists of imports
        """
        return self._imports.copy()

    @property
    def functions(self) -> Dict[Path, List[FunctionInfo]]:
        """Get all discovered functions.

        Returns:
            Dictionary mapping file paths to lists of functions
        """
        return self._functions.copy()

    @property
    def classes(self) -> Dict[Path, List[ClassInfo]]:
        """Get all discovered classes.

        Returns:
            Dictionary mapping file paths to lists of classes
        """
        return self._classes.copy()

    @property
    def framework_info(self) -> Dict[Path, Dict[str, List[dict]]]:
        """Get all discovered framework-specific patterns.

        Returns:
            Dictionary mapping file paths to framework information
        """
        return self._framework_info.copy()

    @property
    def dependency_graph(self) -> DependencyGraph:
        """Get the dependency graph.

        Returns:
            The dependency graph
        """
        return self._dependency_graph


class PythonASTVisitor(ast.NodeVisitor):
    """AST visitor for Python code analysis."""

    def __init__(self):
        """Initialize the visitor."""
        self.imports: List[ImportInfo] = []
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self._current_class: Optional[ClassInfo] = None

    def visit_Import(self, node: ast.Import) -> None:
        """Process Import nodes."""
        for name in node.names:
            self.imports.append(ImportInfo(
                module_name=name.name,
                alias=name.asname,
                line_number=node.lineno
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Process ImportFrom nodes."""
        module = node.module or ""
        for name in node.names:
            self.imports.append(ImportInfo(
                module_name=module,
                imported_names={name.name},
                is_from_import=True,
                alias=name.asname,
                line_number=node.lineno
            ))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Process FunctionDef nodes."""
        self._process_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Process AsyncFunctionDef nodes."""
        self._process_function(node, is_async=True)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Process ClassDef nodes."""
        bases = [self._get_name(base) for base in node.bases]
        decorators = [self._get_name(d) for d in node.decorator_list]

        class_info = ClassInfo(
            name=node.name,
            bases=bases,
            decorators=decorators,
            line_number=node.lineno,
            docstring=ast.get_docstring(node)
        )

        # Set as current class for method detection
        prev_class = self._current_class
        self._current_class = class_info

        # Visit class body
        self.generic_visit(node)

        # Restore previous class context
        self._current_class = prev_class
        self.classes.append(class_info)

    def _process_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], is_async: bool) -> None:
        """Process function definition nodes."""
        args = [arg.arg for arg in node.args.args]
        decorators = [self._get_name(d) for d in node.decorator_list]

        func_info = FunctionInfo(
            name=node.name,
            args=args,
            decorators=decorators,
            is_async=is_async,
            is_method=bool(self._current_class),
            line_number=node.lineno,
            docstring=ast.get_docstring(node)
        )

        if self._current_class:
            self._current_class.methods[node.name] = func_info
        else:
            self.functions.append(func_info)

    def _get_name(self, node: ast.AST) -> str:
        """Get string representation of a name node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return str(node)
