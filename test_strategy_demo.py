import logging
from pathlib import Path

from src.models.dependency_graph import DependencyGraph
from src.models.component import Component
from src.models.relationship import Relationship
from src.models.integration_points.api import APIIntegrationPoint
from src.models.integration_points.database import DatabaseIntegrationPoint
from src.models.integration_points.service import ServiceIntegrationPoint

from src.strategy.approach_recommender import TestApproachRecommender
from src.strategy.test_order.tai_daniels import TaiDanielsOrderGenerator
from src.strategy.test_order.mdtog import MDTOGOrderGenerator
from src.reporting.test_strategy_report import TestStrategyReportGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_strategy_demo")

# Create output directory
output_dir = Path("./output")
output_dir.mkdir(parents=True, exist_ok=True)

# Step 1: Create a dependency graph
# (In a real scenario, this would come from analyzing your codebase)
dependency_graph = DependencyGraph()

# Step 2: Create and add components
components = [
    Component(
        name=f"Component{i}",
        component_type="class",
        location=f"src/module{i}.py",
        complexity_score=0.5 + (i % 3) * 0.1,
        importance_score=0.3 + (i % 5) * 0.1
    )
    for i in range(1, 8)
]

for component in components:
    dependency_graph.add_component(component)

# Step 3: Create and add relationships
relationships = [
    # Component1 has relationships with Component2 and Component3
    Relationship(components[0], components[1], "inheritance", 0.8),
    Relationship(components[0], components[2], "association", 0.5),

    # Component2 has a relationship with Component4
    Relationship(components[1], components[3], "aggregation", 0.7),

    # Component3 has relationships with Component5 and Component6
    Relationship(components[2], components[4], "association", 0.6),
    Relationship(components[2], components[5], "aggregation", 0.4),

    # Component5 has a relationship with Component7
    Relationship(components[4], components[6], "association", 0.5),

    # Create a cycle: Component7 depends on Component2
    Relationship(components[6], components[1], "association", 0.3),
]

for relationship in relationships:
    dependency_graph.add_relationship(relationship)

# Step 4: Create integration points
integration_points = [
    # API Integration Points
    APIIntegrationPoint(
        name="User API",
        location="src/api/user.py",
        integration_type="api",
        source_component="UserController",
        target_component="client",
        http_method="GET",
        route_pattern="/api/users",
        auth_required=True
    ),
    # Database Integration Points
    DatabaseIntegrationPoint(
        name="User Database",
        location="src/repositories/user_repo.py",
        integration_type="database",
        source_component="UserRepository",
        target_component="database",
        db_type="postgresql",
        operation_type="read",
        tables_accessed={"users", "user_roles"}
    ),
    # Service Integration Points
    ServiceIntegrationPoint(
        name="Payment Service",
        location="src/services/payment.py",
        integration_type="service",
        source_component="CheckoutService",
        target_component="PaymentGateway",
        protocol="http",
        service_name="payment-api",
        is_synchronous=True,
        has_timeout=True
    )
]

# Calculate scores for integration points
for point in integration_points:
    if hasattr(point, "calculate_complexity_score"):
        complexity = point.calculate_complexity_score()
        risk = point.calculate_risk_score()
        point.update_scores(complexity, risk)

# Step 5: Generate testing approach recommendation
logger.info("Generating testing approach recommendation")
recommender = TestApproachRecommender(dependency_graph, integration_points)
approach = recommender.recommend_approach()
logger.info(f"Recommended approach: {approach.name} (score: {approach.score:.2f})")

# Step 6: Generate test orders
# Using Tai-Daniels algorithm
logger.info("Generating Tai-Daniels test order")
tai_daniels = TaiDanielsOrderGenerator(dependency_graph)
tai_daniels_result = tai_daniels.generate_order()

# Using MDTOG algorithm
logger.info("Generating MDTOG test order")
mdtog = MDTOGOrderGenerator(dependency_graph)
mdtog_result = mdtog.generate_order()

# Step 7: Generate reports
logger.info("Generating test strategy reports")
report_generator = TestStrategyReportGenerator(dependency_graph, integration_points)

# Generate report for Tai-Daniels algorithm
td_output = output_dir / "tai_daniels"
report_generator.generate_report(
    approach,
    tai_daniels_result,
    str(td_output),
    "Test Strategy Report - Tai-Daniels Algorithm"
)

# Generate report for MDTOG algorithm
mdtog_output = output_dir / "mdtog"
report_generator.generate_report(
    approach,
    mdtog_result,
    str(mdtog_output),
    "Test Strategy Report - MDTOG Algorithm"
)

logger.info(f"Reports generated successfully in {output_dir}")
