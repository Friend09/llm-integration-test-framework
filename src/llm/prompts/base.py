"""Base class for prompt templates."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import json

class PromptTemplate(ABC):
    """Base class for all prompt templates."""

    def __init__(self, template: str):
        """Initialize the prompt template.

        Args:
            template: The template string with placeholders
        """
        self.template = template.strip()

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the expected response.

        Returns:
            A JSON schema describing the expected response structure
        """
        pass

    def format(self, **kwargs: Any) -> str:
        """Format the template with the provided values.

        Args:
            **kwargs: Values to substitute into the template

        Returns:
            The formatted prompt string
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing_key = str(e).strip("'")
            raise ValueError(f"Missing required template value: {missing_key}")
        except Exception as e:
            raise ValueError(f"Error formatting template: {str(e)}")

    def format_with_examples(self, examples: Dict[str, Any], **kwargs: Any) -> str:
        """Format the template with examples and values.

        Args:
            examples: Dictionary of example inputs and outputs
            **kwargs: Values to substitute into the template

        Returns:
            The formatted prompt string with examples
        """
        examples_str = json.dumps(examples, indent=2)
        kwargs["examples"] = examples_str
        return self.format(**kwargs)

    def get_default_system_prompt(self) -> str:
        """Get the default system prompt for this template type.

        Returns:
            A string containing the system prompt
        """
        return (
            "You are an AI assistant helping with software integration testing. "
            "Analyze the provided information and respond in the requested format. "
            "Be precise and thorough in your analysis."
        )

    def get_prompt_with_system(
        self,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Get the complete prompt with system message.

        Args:
            system_prompt: Optional custom system prompt
            **kwargs: Values to substitute into the template

        Returns:
            The complete prompt string
        """
        system = system_prompt or self.get_default_system_prompt()
        formatted = self.format(**kwargs)
        return f"{system}\n\n{formatted}"
