"""Scanner implementation for .NET/C# code analysis."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

from src.scanner.base import BaseScanner
from src.scanner.dependencies import ComponentInfo, DependencyGraph, DependencyInfo
from src.utils.logging import logger


@dataclass
class UsingInfo:
    """Information about a using directive."""
    namespace: str
    alias: Optional[str] = None
    is_static: bool = False
    line_number: int = 0


@dataclass
class PropertyInfo:
    """Information about a property definition."""
    name: str
    type_name: str
    access_modifiers: List[str]
    is_auto_property: bool = True
    line_number: int = 0


@dataclass
class MethodInfo:
    """Information about a method definition."""
    name: str
    return_type: str
    parameters: List[str]
    access_modifiers: List[str]
    attributes: List[str]
    is_async: bool = False
    line_number: int = 0
    docstring: Optional[str] = None


@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    namespace: str
    bases: List[str]
    attributes: List[str]
    methods: Dict[str, MethodInfo] = field(default_factory=dict)
    properties: Dict[str, PropertyInfo] = field(default_factory=dict)
    line_number: int = 0
    docstring: Optional[str] = None


class DotNetScanner(BaseScanner):
    """Scanner for .NET/C# source code files."""

    def __init__(self, *args, **kwargs):
        """Initialize the .NET scanner."""
        super().__init__(*args, **kwargs)
        self._usings: Dict[Path, List[UsingInfo]] = {}
        self._classes: Dict[Path, List[ClassInfo]] = {}
        self._dependency_graph = DependencyGraph()

        # Common C# patterns
        self._patterns = {
            "namespace": re.compile(r"namespace\s+([.\w]+)\s*{?"),
            "using": re.compile(r"using\s+(static\s+)?([.\w]+)(\s+as\s+(\w+))?\s*;"),
            "class": re.compile(r"(?:public|internal|private|protected|static|sealed|abstract)*\s+class\s+(\w+)"),
            "inheritance": re.compile(r":\s*([\w.,\s]+)"),
            "method": re.compile(r"(?:public|private|protected|internal|static|virtual|override|abstract)*\s+(?:async\s+)?[\w<>[\]]+\s+(\w+)\s*\([^)]*\)"),
            "property": re.compile(r"(?:public|private|protected|internal|static|virtual|override)*\s+[\w<>[\]]+\s+(\w+)\s*{\s*get\s*;\s*(?:set\s*;)?}"),
            "attribute": re.compile(r"\[([^\]]+)\]"),
            "doc_comment": re.compile(r"///.*")
        }

    def _default_include_patterns(self) -> List[str]:
        """Return default glob patterns for C# files."""
        return ["**/*.cs"]

    def _default_exclude_patterns(self) -> List[str]:
        """Return default glob patterns to exclude."""
        patterns = super()._default_exclude_patterns()
        patterns.extend([
            "**/bin/**",
            "**/obj/**",
            "**/Debug/**",
            "**/Release/**",
            "**/*.Designer.cs"
        ])
        return patterns

    def scan_file(self, file_path: Path) -> None:
        """Scan a C# file and extract information."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract file components
            namespace = self._extract_namespace(content)
            usings = self._extract_usings(content)
            classes = self._extract_classes(content, namespace)

            # Store extracted information
            if usings:
                self._usings[file_path] = usings
            if classes:
                self._classes[file_path] = classes

            # Add components to dependency graph
            self._add_file_components(file_path, namespace, usings, classes)

        except Exception as e:
            logger.error(f"Error parsing {file_path}: {str(e)}")
            raise

    def _extract_namespace(self, content: str) -> str:
        """Extract namespace from file content."""
        match = self._patterns["namespace"].search(content)
        return match.group(1) if match else ""

    def _extract_usings(self, content: str) -> List[UsingInfo]:
        """Extract using directives from file content."""
        usings = []
        for match in self._patterns["using"].finditer(content):
            usings.append(UsingInfo(
                namespace=match.group(2),
                alias=match.group(4),
                is_static=bool(match.group(1)),
                line_number=content.count("\n", 0, match.start()) + 1
            ))
        return usings

    def _extract_classes(self, content: str, namespace: str) -> List[ClassInfo]:
        """Extract class definitions from file content."""
        classes = []
        lines = content.split("\n")
        current_class = None
        current_doc = []

        for i, line in enumerate(lines):
            # Track XML documentation
            doc_match = self._patterns["doc_comment"].match(line.strip())
            if doc_match:
                current_doc.append(doc_match.group(0).strip("/ "))
                continue

            # Look for class definitions
            class_match = self._patterns["class"].search(line)
            if class_match:
                # Get class attributes
                attributes = []
                j = i - 1
                while j >= 0 and self._patterns["attribute"].match(lines[j].strip()):
                    attr_match = self._patterns["attribute"].match(lines[j].strip())
                    attributes.insert(0, attr_match.group(1))
                    j -= 1

                # Get base classes
                bases = []
                inheritance_match = self._patterns["inheritance"].search(line)
                if inheritance_match:
                    bases = [b.strip() for b in inheritance_match.group(1).split(",")]

                current_class = ClassInfo(
                    name=class_match.group(1),
                    namespace=namespace,
                    bases=bases,
                    attributes=attributes,
                    line_number=i + 1,
                    docstring="\n".join(current_doc) if current_doc else None
                )
                classes.append(current_class)
                current_doc = []
                continue

            # Look for methods in current class
            if current_class:
                method_match = self._patterns["method"].search(line)
                if method_match:
                    # Get method attributes
                    attributes = []
                    j = i - 1
                    while j >= 0 and self._patterns["attribute"].match(lines[j].strip()):
                        attr_match = self._patterns["attribute"].match(lines[j].strip())
                        attributes.insert(0, attr_match.group(1))
                        j -= 1

                    # Parse method signature
                    signature = line.strip()
                    is_async = "async" in signature.lower()
                    access_mods = []
                    for mod in ["public", "private", "protected", "internal", "static", "virtual", "override", "abstract"]:
                        if mod in signature.lower():
                            access_mods.append(mod)

                    current_class.methods[method_match.group(1)] = MethodInfo(
                        name=method_match.group(1),
                        return_type="void",  # This is simplified, would need more parsing for actual type
                        parameters=[],  # This is simplified, would need more parsing for actual parameters
                        access_modifiers=access_mods,
                        attributes=attributes,
                        is_async=is_async,
                        line_number=i + 1,
                        docstring="\n".join(current_doc) if current_doc else None
                    )
                    current_doc = []
                    continue

                # Look for properties
                prop_match = self._patterns["property"].search(line)
                if prop_match:
                    access_mods = []
                    for mod in ["public", "private", "protected", "internal", "static", "virtual", "override"]:
                        if mod in line.lower():
                            access_mods.append(mod)

                    current_class.properties[prop_match.group(1)] = PropertyInfo(
                        name=prop_match.group(1),
                        type_name="object",  # This is simplified, would need more parsing for actual type
                        access_modifiers=access_mods,
                        line_number=i + 1
                    )

        return classes

    def _add_file_components(
        self,
        file_path: Path,
        namespace: str,
        usings: List[UsingInfo],
        classes: List[ClassInfo]
    ) -> None:
        """Add file components to the dependency graph."""
        # Add namespace as a component
        if namespace:
            namespace_component = ComponentInfo(
                name=namespace,
                file_path=file_path,
                component_type="namespace"
            )
            self._dependency_graph.add_component(namespace_component)

        # Add classes as components
        for cls in classes:
            cls_component = ComponentInfo(
                name=f"{cls.namespace}.{cls.name}" if cls.namespace else cls.name,
                file_path=file_path,
                component_type="class",
                is_integration_point=self._is_integration_point(cls)
            )
            self._dependency_graph.add_component(cls_component)

            # Add dependency from namespace to class
            if namespace:
                self._dependency_graph.add_dependency(DependencyInfo(
                    source_file=file_path,
                    source_component=namespace,
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
                    target_file=None,
                    target_component=base,
                    dependency_type="inherits",
                    line_number=cls.line_number
                ))

            # Add method components
            for method_name, method in cls.methods.items():
                method_component = ComponentInfo(
                    name=f"{cls_component.name}.{method_name}",
                    file_path=file_path,
                    component_type="method",
                    is_integration_point=self._is_endpoint(method)
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

        # Add using dependencies
        for using in usings:
            if namespace:
                self._dependency_graph.add_dependency(DependencyInfo(
                    source_file=file_path,
                    source_component=namespace,
                    target_file=None,
                    target_component=using.namespace,
                    dependency_type="using",
                    line_number=using.line_number
                ))

    def _is_integration_point(self, cls: ClassInfo) -> bool:
        """Check if a class is an integration point."""
        integration_bases = {
            "Controller", "ControllerBase",  # ASP.NET Controllers
            "Hub",  # SignalR
            "BackgroundService",  # Background workers
            "IHostedService"  # Hosted services
        }

        return (
            any(base.endswith(tuple(integration_bases)) for base in cls.bases) or
            any("Controller" in attr or "ApiController" in attr for attr in cls.attributes)
        )

    def _is_endpoint(self, method: MethodInfo) -> bool:
        """Check if a method is an API endpoint."""
        endpoint_attributes = {
            "HttpGet", "HttpPost", "HttpPut", "HttpDelete",  # ASP.NET Core
            "Route", "ApiRoute",  # General routing
            "ServiceFilter", "TypeFilter"  # Filters that might indicate endpoints
        }

        return any(
            any(attr.startswith(ep) for ep in endpoint_attributes)
            for attr in method.attributes
        )

    @property
    def dependency_graph(self) -> DependencyGraph:
        """Get the dependency graph."""
        return self._dependency_graph
