"""Mock LLM client for testing."""
import json
import logging
from typing import Any, Dict, List, Optional, Union

from .base import LLMClient, LLMError, ValidationError

logger = logging.getLogger(__name__)

class MockLLMClient(LLMClient):
    """Mock LLM client for testing purposes."""

    def __init__(
        self,
        responses: Optional[Dict[str, str]] = None,
        json_responses: Optional[Dict[str, Dict[str, Any]]] = None,
        token_count: int = 1,
        should_fail: bool = False
    ):
        """Initialize the mock client.

        Args:
            responses: Dictionary mapping prompts to responses
            json_responses: Dictionary mapping prompts to JSON responses
            token_count: Mock token count to return
            should_fail: Whether the client should simulate failures
        """
        self.responses = responses or {}
        self.json_responses = json_responses or {}
        self.token_count = token_count
        self.should_fail = should_fail
        self.calls = []  # Track calls for testing
        super().__init__()

    def _setup_client(self) -> None:
        """Mock setup - no actual setup needed."""
        pass

    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """Mock generate method.

        Args:
            prompt: The input prompt
            temperature: Ignored in mock
            max_tokens: Ignored in mock
            stop_sequences: Ignored in mock
            **kwargs: Ignored in mock

        Returns:
            A mock response based on the prompt

        Raises:
            LLMError: If should_fail is True or prompt not found
        """
        self.calls.append({
            "method": "generate",
            "prompt": prompt,
            "kwargs": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stop_sequences": stop_sequences,
                **kwargs
            }
        })

        if self.should_fail:
            raise LLMError("Mock LLM failure")

        if prompt in self.responses:
            return self.responses[prompt]

        # Default mock response
        return f"Mock response for: {prompt[:50]}..."

    async def generate_json(
        self,
        prompt: str,
        *,
        schema: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Mock JSON generation.

        Args:
            prompt: The input prompt
            schema: JSON schema (used for mock response if no preset)
            **kwargs: Ignored in mock

        Returns:
            A mock JSON response

        Raises:
            LLMError: If should_fail is True
            ValidationError: If mock response doesn't match schema
        """
        self.calls.append({
            "method": "generate_json",
            "prompt": prompt,
            "schema": schema,
            "kwargs": kwargs
        })

        if self.should_fail:
            raise LLMError("Mock LLM failure")

        if prompt in self.json_responses:
            return self.json_responses[prompt]

        # Generate a mock response based on the schema
        mock_response = self._generate_mock_response(schema)
        return mock_response

    def get_token_count(self, text: str) -> int:
        """Mock token counting.

        Args:
            text: The input text

        Returns:
            The configured mock token count
        """
        return self.token_count

    def _generate_mock_response(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock response that matches the schema structure.

        Args:
            schema: The JSON schema to match

        Returns:
            A mock response matching the schema structure
        """
        if "type" not in schema:
            return {}

        if schema["type"] == "object":
            result = {}
            for prop, details in schema.get("properties", {}).items():
                result[prop] = self._generate_mock_value(details)
            return result

        return self._generate_mock_value(schema)

    def _generate_mock_value(self, schema: Dict[str, Any]) -> Any:
        """Generate a mock value based on the schema type.

        Args:
            schema: Schema for the value to generate

        Returns:
            A mock value matching the schema type
        """
        schema_type = schema.get("type", "string")

        if schema_type == "string":
            return "mock_string"
        elif schema_type == "number":
            return 42
        elif schema_type == "integer":
            return 42
        elif schema_type == "boolean":
            return True
        elif schema_type == "array":
            return [self._generate_mock_value(schema.get("items", {}))]
        elif schema_type == "object":
            return self._generate_mock_response(schema)
        else:
            return None
