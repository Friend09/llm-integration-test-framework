"""Base interface for LLM clients."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM client.

        Args:
            api_key: Optional API key for authentication. If not provided,
                    will attempt to load from environment variables.
        """
        self.api_key = api_key
        self._setup_client()

    @abstractmethod
    def _setup_client(self) -> None:
        """Set up the client with API key and any necessary configuration.

        This method should be implemented by subclasses to handle their specific
        initialization requirements.
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt to send to the LLM
            temperature: Controls randomness in the output (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            stop_sequences: Optional list of sequences where generation should stop
            **kwargs: Additional model-specific parameters

        Returns:
            The generated text response

        Raises:
            LLMError: If there is an error communicating with the LLM
        """
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        *,
        schema: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Generate a JSON response from the LLM.

        Args:
            prompt: The input prompt to send to the LLM
            schema: JSON schema that the response should conform to
            **kwargs: Additional generation parameters

        Returns:
            The generated response as a Python dictionary

        Raises:
            LLMError: If there is an error communicating with the LLM
            ValidationError: If the response doesn't match the schema
        """
        pass

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Get the number of tokens in the given text.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text
        """
        pass

class LLMError(Exception):
    """Base exception class for LLM-related errors."""
    pass

class ValidationError(LLMError):
    """Raised when LLM response validation fails."""
    pass

class TokenLimitError(LLMError):
    """Raised when token limits are exceeded."""
    pass
