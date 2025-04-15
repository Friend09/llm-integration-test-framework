"""Database integration point class for representing database interactions."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .base import IntegrationPoint


@dataclass
class DatabaseIntegrationPoint(IntegrationPoint):
    """Represents a database interaction point in the system."""

    db_type: str = "unknown"  # Type of database (e.g., PostgreSQL, MySQL, MongoDB)
    operation_type: str = "read"  # Type of operation (read, write, delete, etc.)
    tables_accessed: Set[str] = field(default_factory=set)  # Tables/collections accessed
    uses_transactions: bool = False  # Whether transactions are used
    uses_orm: bool = False  # Whether an ORM is used
    query_complexity: float = 0.0  # Complexity score for the query (0.0 to 1.0)
    involves_joins: bool = False  # Whether the operation involves joins
    is_bulk_operation: bool = False  # Whether it's a bulk operation

    def to_dict(self) -> Dict:
        """Convert the database integration point to a dictionary representation."""
        base_dict = super().to_dict()
        db_dict = {
            "db_type": self.db_type,
            "operation_type": self.operation_type,
            "tables_accessed": list(self.tables_accessed),
            "uses_transactions": self.uses_transactions,
            "uses_orm": self.uses_orm,
            "query_complexity": self.query_complexity,
            "involves_joins": self.involves_joins,
            "is_bulk_operation": self.is_bulk_operation
        }
        return {**base_dict, **db_dict}

    @classmethod
    def from_dict(cls, data: Dict) -> "DatabaseIntegrationPoint":
        """Create a DatabaseIntegrationPoint instance from a dictionary."""
        if "tables_accessed" in data:
            data["tables_accessed"] = set(data["tables_accessed"])
        return cls(**data)

    def calculate_complexity_score(self) -> float:
        """Calculate complexity score based on database operation characteristics."""
        score = 0.0

        # Base complexity from query complexity
        score += self.query_complexity * 0.3

        # Complexity from number of tables accessed
        table_count = len(self.tables_accessed)
        score += min(0.2, table_count * 0.05)  # Cap at 0.2

        # Additional complexity factors
        if self.uses_transactions:
            score += 0.15
        if self.involves_joins:
            score += 0.15
        if self.is_bulk_operation:
            score += 0.1
        if self.operation_type in ["write", "delete"]:
            score += 0.1

        # Normalize score to 0-1 range
        return min(1.0, score)

    def calculate_risk_score(self) -> float:
        """Calculate risk score based on database operation characteristics."""
        score = 0.0

        # Higher risk for write/delete operations
        if self.operation_type in ["write", "delete"]:
            score += 0.3

        # Risk based on number of tables affected
        table_count = len(self.tables_accessed)
        score += min(0.2, table_count * 0.05)  # Cap at 0.2

        # Additional risk factors
        if self.uses_transactions:
            score += 0.15  # Transaction failure risk
        if self.is_bulk_operation:
            score += 0.15  # Bulk operation risks
        if self.involves_joins:
            score += 0.1  # Join complexity risks
        if not self.uses_orm:
            score += 0.1  # Raw SQL risks

        # Normalize score to 0-1 range
        return min(1.0, score)

    def generate_test_requirements(self) -> List[str]:
        """Generate a list of test requirements for this database operation."""
        requirements = [
            f"Test {self.operation_type} operation on {', '.join(self.tables_accessed)}"
        ]

        if self.uses_transactions:
            requirements.extend([
                "Test successful transaction completion",
                "Test transaction rollback on error",
                "Test concurrent transactions"
            ])

        if self.involves_joins:
            requirements.extend([
                "Test join operation correctness",
                "Test join performance",
                "Test with missing related records"
            ])

        if self.is_bulk_operation:
            requirements.extend([
                "Test bulk operation success",
                "Test partial failure handling",
                "Test performance with large datasets"
            ])

        if self.operation_type in ["write", "delete"]:
            requirements.extend([
                "Test data integrity constraints",
                "Test concurrent modifications",
                "Test failure recovery"
            ])

        requirements.extend([
            "Test error handling",
            "Test connection failure recovery",
            "Test query timeout handling"
        ])

        return requirements

    def add_table(self, table_name: str) -> None:
        """Add a table/collection to the list of accessed tables."""
        self.tables_accessed.add(table_name)

    def update_query_complexity(self, complexity: float) -> None:
        """Update the query complexity score."""
        if not 0.0 <= complexity <= 1.0:
            raise ValueError("Query complexity must be between 0.0 and 1.0")
        self.query_complexity = complexity
