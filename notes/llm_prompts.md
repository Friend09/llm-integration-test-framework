# LLM Prompt Templates Documentation

This document provides detailed information about the LLM prompt templates used in the framework for automated test analysis and generation.

## Overview

The framework uses four main prompt templates that work together to provide comprehensive test analysis:

1. Test Requirements Prompt
2. Risk Assessment Prompt
3. Complexity Assessment Prompt
4. Test Recommendations Prompt

## Test Requirements Prompt

The `TestRequirementsPrompt` generates specific test requirements based on component analysis.

### Usage

```python
from src.llm.prompts.test_requirements import TestRequirementsPrompt

prompt = TestRequirementsPrompt()
response = await llm_client.generate(
    prompt,
    component_analysis=component_analysis,
    integration_points=integration_points,
    dependencies=dependencies,
    resource_constraints=resource_constraints  # Optional
)
```

### Response Schema

```json
{
    "test_requirements": [
        {
            "name": "string",
            "description": "string",
            "prerequisites": ["string"],
            "validation_criteria": ["string"],
            "dependencies": ["string"],
            "priority": "high|medium|low"
        }
    ],
    "coverage_requirements": {
        "unit_test_coverage": number,
        "integration_test_coverage": number,
        "e2e_test_coverage": number
    }
}
```

## Risk Assessment Prompt

The `TestRiskAssessmentPrompt` evaluates potential risks and their impact on testing.

### Usage

```python
from src.llm.prompts.test_risk_assessment import TestRiskAssessmentPrompt

prompt = TestRiskAssessmentPrompt()
response = await llm_client.generate(
    prompt,
    test_requirements=test_requirements,
    component_analysis=component_analysis,
    integration_points=integration_points,
    dependencies=dependencies,
    resource_constraints=resource_constraints  # Optional
)
```

### Response Schema

```json
{
    "risk_factors": [
        {
            "name": "string",
            "description": "string",
            "impact": "high|medium|low",
            "probability": "high|medium|low",
            "mitigation_strategy": "string",
            "affected_components": ["string"]
        }
    ],
    "overall_risk_assessment": {
        "risk_level": "high|medium|low",
        "key_concerns": ["string"],
        "recommendations": ["string"]
    }
}
```

## Complexity Assessment Prompt

The `TestComplexityAssessmentPrompt` analyzes testing complexity and resource requirements.

### Usage

```python
from src.llm.prompts.test_complexity_assessment import TestComplexityAssessmentPrompt

prompt = TestComplexityAssessmentPrompt()
response = await llm_client.generate(
    prompt,
    test_requirements=test_requirements,
    component_analysis=component_analysis,
    integration_points=integration_points,
    dependencies=dependencies,
    resource_constraints=resource_constraints  # Optional
)
```

### Response Schema

```json
{
    "component_complexity": [
        {
            "component_name": "string",
            "cyclomatic_complexity": number,
            "integration_complexity": number,
            "data_complexity": number,
            "test_effort_estimate": "high|medium|low",
            "required_expertise_level": "expert|intermediate|beginner",
            "complexity_factors": ["string"]
        }
    ],
    "overall_assessment": {
        "total_complexity_score": number,
        "estimated_testing_time": "string",
        "resource_requirements": {
            "team_size": number,
            "required_skills": ["string"],
            "tools_needed": ["string"]
        },
        "recommendations": ["string"]
    }
}
```

## Test Recommendations Prompt

The `TestRecommendationsPrompt` provides specific testing approaches and best practices.

### Usage

```python
from src.llm.prompts.test_recommendations import TestRecommendationsPrompt

prompt = TestRecommendationsPrompt()
response = await llm_client.generate(
    prompt,
    test_requirements=test_requirements,
    complexity_assessment=complexity_assessment,
    risk_assessment=risk_assessment,
    component_analysis=component_analysis,
    integration_points=integration_points,
    resource_constraints=resource_constraints  # Optional
)
```

### Response Schema

```json
{
    "testing_approaches": [
        {
            "name": "string",
            "description": "string",
            "benefits": ["string"],
            "limitations": ["string"],
            "tools": ["string"],
            "best_practices": ["string"]
        }
    ],
    "framework_recommendations": {
        "recommended_frameworks": [
            {
                "name": "string",
                "purpose": "string",
                "version": "string",
                "justification": "string"
            }
        ],
        "setup_guidelines": ["string"],
        "integration_tips": ["string"]
    }
}
```

## Integration Example

Here's a complete example of using all prompts together:

```python
from src.analysis.llm_analysis import LLMAnalysis

# Initialize the analyzer
analyzer = LLMAnalysis(
    repo_url="https://github.com/example/repo",
    output_dir="output/llm_analysis"
)

# Run the analysis
results = await analyzer.analyze()

# Access results
test_requirements = results["test_requirements"]
risk_assessment = results["risk_assessment"]
complexity_assessment = results["complexity_assessment"]
recommendations = results["recommendations"]
```

## Best Practices

1. **Environment Setup**
   - Ensure OpenAI API key is properly configured
   - Use appropriate model version for your needs
   - Set up proper error handling and logging

2. **Resource Management**
   - Monitor API usage and costs
   - Implement rate limiting if needed
   - Cache results when possible

3. **Response Handling**
   - Validate responses against schemas
   - Implement proper error handling
   - Save results for future reference

4. **Integration**
   - Use the provided `LLMAnalysis` class for complete analysis
   - Customize prompts as needed for specific use cases
   - Implement proper logging and monitoring

## Troubleshooting

Common issues and solutions:

1. **API Errors**
   - Check API key configuration
   - Verify network connectivity
   - Monitor rate limits

2. **Response Validation**
   - Ensure responses match expected schemas
   - Implement proper error handling
   - Log validation failures

3. **Performance Issues**
   - Implement caching where possible
   - Use appropriate model sizes
   - Monitor and optimize API calls

## Support

For issues or questions:
- Check the project documentation
- Open an issue on GitHub
- Contact the development team
