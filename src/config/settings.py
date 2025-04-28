"""Configuration management for the LLM Integration Testing Framework."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field, SecretStr


class LLMConfig(BaseModel):
    """Configuration for LLM integration."""
    api_key: SecretStr = Field(..., env='OPENAI_API_KEY')
    model: str = Field(default="gpt-4", env='OPENAI_MODEL')
    temperature: float = Field(default=0.0, env='OPENAI_TEMPERATURE')
    max_tokens: int = Field(default=2000, env='OPENAI_MAX_TOKENS')


class GitHubConfig(BaseModel):
    """Configuration for GitHub integration."""
    token: Optional[SecretStr] = Field(default=None, env='GITHUB_TOKEN')
    api_url: str = Field(default="https://api.github.com", env='GITHUB_API_URL')


class AnalysisConfig(BaseModel):
    """Configuration for code analysis."""
    max_file_size: int = Field(default=1_000_000, env='MAX_FILE_SIZE')  # 1MB
    exclude_patterns: list[str] = Field(
        default=["**/tests/*", "**/venv/*", "**/.git/*"],
        env='EXCLUDE_PATTERNS'
    )
    include_patterns: list[str] = Field(
        default=["**/*.py", "**/*.cs"],
        env='INCLUDE_PATTERNS'
    )


class OutputConfig(BaseModel):
    """Configuration for report generation."""
    output_dir: Path = Field(default=Path("reports"), env='OUTPUT_DIR')
    report_format: str = Field(default="html", env='REPORT_FORMAT')
    include_visualizations: bool = Field(default=True, env='INCLUDE_VISUALIZATIONS')


@dataclass
class Config:
    """Main configuration class that loads and manages all settings."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from environment variables and config file.

        Args:
            config_file: Optional path to YAML configuration file.
        """
        if hasattr(self, '_initialized'):
            return

        # Load config file if provided
        config_data = {}
        if config_file:
            config_data = self._load_yaml_config(config_file)

        # Initialize each config section
        self.llm = LLMConfig(**config_data.get('llm', {}))
        self.github = GitHubConfig(**config_data.get('github', {}))
        self.analysis = AnalysisConfig(**config_data.get('analysis', {}))
        self.output = OutputConfig(**config_data.get('output', {}))

        self._initialized = True

    @staticmethod
    def _load_yaml_config(config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Args:
            config_file: Path to YAML configuration file.

        Returns:
            Dictionary containing configuration values.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing configuration file: {e}")

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as a dictionary.

        Returns:
            Dictionary containing all configuration values.
        """
        return {
            'llm': self.llm.model_dump(exclude={'api_key'}),
            'github': self.github.model_dump(exclude={'token'}),
            'analysis': self.analysis.model_dump(),
            'output': self.output.model_dump()
        }


# Global configuration instance
config = Config()
