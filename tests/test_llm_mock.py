"""Tests for the mock LLM client and response parser."""
import pytest
from typing import Dict, Any

from src.llm.mock import MockLLMClient
from src.llm.parser import ResponseParser
from src.llm.base import ValidationError

@pytest.fixture
def mock_client():
    """Create a mock client with test responses."""
    responses = {
        "list test": "1. First item\n2. Second item\n- Third item",
        "key value test": "key1: value1\nkey2: value2\ninvalid line\nkey3: value3",
        "structured test": "Field1: Value1\nField2: Value2\nField3: Value3",
    }

    json_responses = {
        "json test": {
            "name": "Test Component",
            "type": "module",
            "properties": ["prop1", "prop2"]
        }
    }

    return MockLLMClient(responses=responses, json_responses=json_responses)

@pytest.mark.asyncio
async def test_mock_json_generation():
    """Test JSON response generation and validation."""
    client = MockLLMClient(json_responses={
        "test": {"name": "test", "value": 42}
    })

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "integer"}
        },
        "required": ["name", "value"]
    }

    result = await client.generate_json("test", schema=schema)
    assert result == {"name": "test", "value": 42}

@pytest.mark.asyncio
async def test_mock_json_validation_error():
    """Test JSON validation error handling."""
    client = MockLLMClient(json_responses={
        "test": {"name": "test"}  # Missing required 'value' field
    })

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "integer"}
        },
        "required": ["name", "value"]
    }

    with pytest.raises(ValidationError):
        await client.generate_json("test", schema=schema)

def test_parse_list():
    """Test list response parsing."""
    response = "1. First item\n2. Second item\n- Third item\n* Fourth item"
    result = ResponseParser.parse_list(response)
    assert result == ["First item", "Second item", "Third item", "Fourth item"]

def test_parse_key_value():
    """Test key-value response parsing."""
    response = "key1: value1\nkey2: value2\ninvalid line\nkey3: value3"
    result = ResponseParser.parse_key_value(response)
    assert result == {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }

def test_parse_structured():
    """Test structured response parsing."""
    response = "Field1: Value1\nField2: Value2\nField3: Value3"
    expected_fields = ["Field1", "Field2", "Field3"]
    result = ResponseParser.parse_structured(response, expected_fields)
    assert result == {
        "Field1": "Value1",
        "Field2": "Value2",
        "Field3": "Value3"
    }

def test_parse_structured_missing_required():
    """Test structured response parsing with missing required fields."""
    response = "Field1: Value1\nField3: Value3"
    expected_fields = ["Field1", "Field2", "Field3"]
    required_fields = ["Field1", "Field2"]

    with pytest.raises(ValidationError):
        ResponseParser.parse_structured(
            response,
            expected_fields,
            required_fields=required_fields
        )

@pytest.mark.asyncio
async def test_mock_failure():
    """Test mock client failure simulation."""
    client = MockLLMClient(should_fail=True)

    with pytest.raises(ValidationError):
        await client.generate("test prompt")

def test_parse_json_markdown():
    """Test JSON parsing with markdown code blocks."""
    response = '''```json
{
    "name": "test",
    "value": 42
}
```'''

    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "integer"}
        },
        "required": ["name", "value"]
    }

    result = ResponseParser.parse_json(response, schema)
    assert result == {"name": "test", "value": 42}

def test_parse_json_non_strict():
    """Test JSON parsing in non-strict mode."""
    response = '{"name": "test", "extra": "field"}'
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "integer"}
        },
        "required": ["name"]
    }

    result = ResponseParser.parse_json(response, schema, strict=False)
    assert result["name"] == "test"
