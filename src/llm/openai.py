"""OpenAI API client implementation."""
import os
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

import openai
import tiktoken
from openai import AsyncOpenAI, OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from .base import LLMClient, LLMError, ValidationError, TokenLimitError

logger = logging.getLogger(__name__)

class OpenAIClient(LLMClient):
    """OpenAI API client implementation."""

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1
    MAX_RETRY_DELAY = 10

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        cache_size: int = 100
    ):
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key. If not provided, will try to load from
                    OPENAI_API_KEY environment variable.
            model: The model to use for generation (default: gpt-4-turbo-preview)
            cache_size: Size of the LRU cache for responses
        """
        self.model = model
        super().__init__(api_key)

    def _setup_client(self) -> None:
        """Set up the OpenAI client with API key."""
        self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=30.0,
        )
        self.sync_client = OpenAI(
            api_key=self.api_key,
            timeout=30.0,
        )
        self.encoding = tiktoken.encoding_for_model(self.model)

    @retry(
        retry=retry_if_exception_type(openai.RateLimitError),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY, max=MAX_RETRY_DELAY)
    )
    async def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """Generate a response from the OpenAI API.

        Args:
            prompt: The input prompt to send to the model
            temperature: Controls randomness in the output (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            stop_sequences: Optional list of sequences where generation should stop
            **kwargs: Additional parameters to pass to the API

        Returns:
            The generated text response

        Raises:
            LLMError: If there is an error communicating with the API
            TokenLimitError: If the prompt exceeds the model's token limit
        """
        try:
            # Check token count
            prompt_tokens = self.get_token_count(prompt)
            if max_tokens and prompt_tokens + max_tokens > self.get_model_token_limit():
                raise TokenLimitError(f"Total tokens would exceed model limit")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop_sequences,
                **kwargs
            )

            return response.choices[0].message.content

        except openai.APIError as e:
            raise LLMError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise LLMError(f"Unexpected error: {str(e)}")

    async def generate_json(
        self,
        prompt: str,
        *,
        schema: Dict[str, Any],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Generate a JSON response from the OpenAI API.

        Args:
            prompt: The input prompt to send to the model
            schema: JSON schema that the response should conform to
            **kwargs: Additional generation parameters

        Returns:
            The generated response as a Python dictionary

        Raises:
            LLMError: If there is an error communicating with the API
            ValidationError: If the response doesn't match the schema
        """
        # Add schema to the prompt
        schema_prompt = (
            f"{prompt}\n\nRespond with a JSON object that matches this schema:\n"
            f"{json.dumps(schema, indent=2)}"
        )

        try:
            response = await self.generate(
                schema_prompt,
                temperature=0.1,  # Lower temperature for more deterministic JSON
                **kwargs
            )

            # Extract JSON from response
            try:
                json_str = response.strip()
                if json_str.startswith("```json"):
                    json_str = json_str.split("```json")[1]
                if json_str.endswith("```"):
                    json_str = json_str.rsplit("```", 1)[0]

                data = json.loads(json_str.strip())

                # TODO: Add JSON schema validation here
                return data

            except json.JSONDecodeError as e:
                raise ValidationError(f"Failed to parse JSON response: {str(e)}")

        except LLMError as e:
            raise LLMError(f"Error generating JSON response: {str(e)}")

    def get_token_count(self, text: str) -> int:
        """Get the number of tokens in the given text.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text
        """
        return len(self.encoding.encode(text))

    def get_model_token_limit(self) -> int:
        """Get the token limit for the current model.

        Returns:
            The maximum number of tokens the model can handle
        """
        # Model token limits
        limits = {
            "gpt-4-turbo-preview": 128000,
            "gpt-4": 8192,
            "gpt-3.5-turbo": 4096,
        }
        return limits.get(self.model, 4096)  # Default to 4096 if model not found
