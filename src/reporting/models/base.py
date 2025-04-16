"""Base report models for the LLM Integration Testing Framework."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class ReportSection(ABC):
    """Base class for all report sections."""

    title: str
    template_name: str
    data: Dict[str, Any]

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a report section.

        Args:
            data: Dictionary containing section data
        """
        self.data = data
        self._process_data()

    @abstractmethod
    def _process_data(self) -> None:
        """Process raw data into section-specific format."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert section to dictionary format.

        Returns:
            Dict containing section data
        """
        return {
            "title": self.title,
            "template_name": self.template_name,
            "data": self.data
        }

    def __str__(self) -> str:
        """Return string representation of section."""
        return f"{self.title} Section"

class ReportSectionInterface(ABC):
    """Interface for report sections."""

    @abstractmethod
    def generate_content(self) -> Dict[str, Any]:
        """Generate section content."""
        pass

    @abstractmethod
    def validate_content(self) -> bool:
        """Validate section content."""
        pass

@dataclass
class Report:
    """Base report class."""
    title: str
    sections: List[ReportSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def add_section(self, section: ReportSection) -> None:
        """Add a section to the report."""
        self.sections.append(section)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return {
            "title": self.title,
            "sections": [section.to_dict() for section in self.sections],
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
