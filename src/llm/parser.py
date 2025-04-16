"""Response parser for LLM outputs."""
import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar, Union

import jsonschema
from jsonschema import ValidationError as JsonSchemaValidationError

from .base import ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ResponseParser:
    """Parser for LLM responses."""

    @staticmethod
    def parse_json(
        response: str,
        schema: Dict[str, Any],
        *,
        strict: bool = True
    ) -> Dict[str, Any]:
        """Parse a JSON response from the LLM.

        Args:
            response: The raw response from the LLM
            schema: JSON schema to validate against
            strict: Whether to enforce strict schema validation

        Returns:
            The parsed JSON data

        Raises:
            ValidationError: If the response cannot be parsed or doesn't match schema
        """
        # Extract JSON from response (handle markdown code blocks)
        json_str = response.strip()
        if json_str.startswith("```json"):
            json_str = json_str.split("```json")[1]
        if json_str.endswith("```"):
            json_str = json_str.rsplit("```", 1)[0]
        json_str = json_str.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Failed to parse JSON response: {str(e)}")

        try:
            if strict:
                jsonschema.validate(instance=data, schema=schema)
            else:
                # In non-strict mode, only validate required fields
                required_schema = ResponseParser._get_required_schema(schema)
                jsonschema.validate(instance=data, schema=required_schema)
        except JsonSchemaValidationError as e:
            raise ValidationError(f"Response does not match schema: {str(e)}")

        return data

    @staticmethod
    def parse_list(response: str, *, delimiter: str = "\n") -> list[str]:
        """Parse a list response from the LLM.

        Args:
            response: The raw response from the LLM
            delimiter: The delimiter to split on (default: newline)

        Returns:
            List of strings from the response
        """
        # Remove markdown list markers and clean up
        lines = [
            line.strip().lstrip("*-").strip()
            for line in response.strip().split(delimiter)
        ]
        return [line for line in lines if line]

    @staticmethod
    def parse_key_value(response: str) -> Dict[str, str]:
        """Parse a key-value response from the LLM.

        Args:
            response: The raw response from the LLM

        Returns:
            Dictionary of key-value pairs

        Raises:
            ValidationError: If the response cannot be parsed as key-value pairs
        """
        result = {}
        lines = response.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or ":" not in line:
                continue

            try:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
            except ValueError:
                logger.warning(f"Skipping invalid key-value line: {line}")

        if not result:
            raise ValidationError("No valid key-value pairs found in response")

        return result

    @staticmethod
    def parse_structured(
        response: str,
        expected_fields: list[str],
        *,
        required_fields: Optional[list[str]] = None
    ) -> Dict[str, str]:
        """Parse a structured text response from the LLM.

        Args:
            response: The raw response from the LLM
            expected_fields: List of field names to look for
            required_fields: List of required field names (default: all fields)

        Returns:
            Dictionary of field values

        Raises:
            ValidationError: If required fields are missing
        """
        result = {}
        required = required_fields or expected_fields

        # Look for each field in the response
        for field in expected_fields:
            field_lower = field.lower()

            # Try to find the field in the response
            for line in response.split("\n"):
                line = line.strip()
                if line.lower().startswith(field_lower + ":"):
                    value = line[len(field) + 1:].strip()
                    result[field] = value
                    break

        # Check required fields
        missing = [f for f in required if f not in result]
        if missing:
            raise ValidationError(f"Missing required fields: {', '.join(missing)}")

        return result

    @staticmethod
    def _get_required_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Get a schema that only enforces required fields.

        Args:
            schema: The full JSON schema

        Returns:
            A modified schema that only validates required fields
        """
        required_schema = schema.copy()

        if "properties" in required_schema:
            new_properties = {}
            required_fields = required_schema.get("required", [])

            for field in required_fields:
                if field in required_schema["properties"]:
                    new_properties[field] = required_schema["properties"][field]

            required_schema["properties"] = new_properties

        return required_schema
