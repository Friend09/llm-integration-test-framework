"""Component dependency analysis functionality."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Union


@dataclass
class DependencyInfo:
    """Information about a dependency between components."""
    source_file: Path
    source_component: str
    target_file: Optional[Path]
    target_component: str
    dependency_type: str  # 'import', 'inheritance', 'usage', etc.
    line_number: int


@dataclass
class ComponentInfo:
    """Information about a component and its dependencies."""
    name: str
    file_path: Path
    component_type: str  # 'class', 'function', 'module'
    dependencies: Set[DependencyInfo] = field(default_factory=set)
    dependents: Set[DependencyInfo] = field(default_factory=set)
    framework_type: Optional[str] = None  # 'flask', 'django', 'fastapi', etc.
    is_integration_point: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


class DependencyGraph:
    """Graph representation of component dependencies."""

    def __init__(self):
        """Initialize the dependency graph."""
        self._components: Dict[str, ComponentInfo] = {}
        self._file_components: Dict[Path, Set[str]] = {}

    def add_component(self, component: ComponentInfo) -> None:
        """Add a component to the graph.

        Args:
            component: Component information
        """
        self._components[component.name] = component
        if component.file_path not in self._file_components:
            self._file_components[component.file_path] = set()
        self._file_components[component.file_path].add(component.name)

    def add_dependency(self, dependency: DependencyInfo) -> None:
        """Add a dependency between components.

        Args:
            dependency: Dependency information
        """
        if dependency.source_component in self._components:
            self._components[dependency.source_component].dependencies.add(dependency)

        if dependency.target_component in self._components:
            self._components[dependency.target_component].dependents.add(dependency)

    def get_component(self, name: str) -> Optional[ComponentInfo]:
        """Get component information by name.

        Args:
            name: Component name

        Returns:
            Component information if found
        """
        return self._components.get(name)

    def get_file_components(self, file_path: Path) -> Set[str]:
        """Get all components in a file.

        Args:
            file_path: Path to the file

        Returns:
            Set of component names
        """
        return self._file_components.get(file_path, set())

    def get_dependencies(self, component_name: str) -> Set[DependencyInfo]:
        """Get all dependencies of a component.

        Args:
            component_name: Name of the component

        Returns:
            Set of dependencies
        """
        component = self._components.get(component_name)
        return component.dependencies if component else set()

    def get_dependents(self, component_name: str) -> Set[DependencyInfo]:
        """Get all components that depend on this component.

        Args:
            component_name: Name of the component

        Returns:
            Set of dependencies
        """
        component = self._components.get(component_name)
        return component.dependents if component else set()

    def get_integration_points(self) -> List[ComponentInfo]:
        """Get all components marked as integration points.

        Returns:
            List of integration point components
        """
        return [
            component for component in self._components.values()
            if component.is_integration_point
        ]

    def get_framework_components(self, framework: str) -> List[ComponentInfo]:
        """Get all components associated with a framework.

        Args:
            framework: Framework name ('flask', 'django', etc.)

        Returns:
            List of framework components
        """
        return [
            component for component in self._components.values()
            if component.framework_type == framework
        ]

    def find_cycles(self) -> List[List[str]]:
        """Find cyclic dependencies in the graph.

        Returns:
            List of cycles, where each cycle is a list of component names
        """
        cycles = []
        visited = set()
        path = []

        def dfs(component: str) -> None:
            if component in path:
                cycle_start = path.index(component)
                cycles.append(path[cycle_start:])
                return

            if component in visited:
                return

            visited.add(component)
            path.append(component)

            for dep in self.get_dependencies(component):
                dfs(dep.target_component)

            path.pop()

        for component in self._components:
            if component not in visited:
                dfs(component)

        return cycles

    def calculate_complexity(self, component_name: str) -> int:
        """Calculate complexity score for a component.

        Args:
            component_name: Name of the component

        Returns:
            Complexity score based on dependencies
        """
        component = self._components.get(component_name)
        if not component:
            return 0

        # Base score
        score = 1

        # Add points for each dependency and dependent
        score += len(component.dependencies)
        score += len(component.dependents)

        # Extra points for being an integration point
        if component.is_integration_point:
            score += 5

        # Extra points for framework components
        if component.framework_type:
            score += 3

        return score

    def get_critical_components(self, threshold: int = 5) -> List[ComponentInfo]:
        """Get components with high complexity/connectivity.

        Args:
            threshold: Minimum complexity score to be considered critical

        Returns:
            List of critical components
        """
        return [
            component for component in self._components.values()
            if self.calculate_complexity(component.name) >= threshold
        ]

    def to_dict(self) -> Dict:
        """Convert the graph to a dictionary representation.

        Returns:
            Dictionary containing graph data
        """
        return {
            "components": {
                name: {
                    "name": comp.name,
                    "file": str(comp.file_path),
                    "type": comp.component_type,
                    "framework": comp.framework_type,
                    "is_integration_point": comp.is_integration_point,
                    "dependencies": [
                        {
                            "target": dep.target_component,
                            "type": dep.dependency_type,
                            "line": dep.line_number
                        }
                        for dep in comp.dependencies
                    ],
                    "metadata": comp.metadata
                }
                for name, comp in self._components.items()
            }
        }
