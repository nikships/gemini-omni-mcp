"""Configuration settings for the Gemini Omni MCP server."""

import os
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .constants import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_DELIVERY,
    DEFAULT_DURATION_SECONDS,
    DEFAULT_ENHANCEMENT_MODEL,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_TIMEOUT,
    FILE_POLL_INTERVAL,
    FILE_POLL_TIMEOUT,
    MAX_BATCH_SIZE,
)

_ENV_CONFIG = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
)


class ServerConfig(BaseSettings):
    """Server configuration settings."""

    model_config = _ENV_CONFIG

    log_level: str = Field(default="INFO", description="Logging level")
    output_dir: str = Field(default=DEFAULT_OUTPUT_DIR, description="Generated video directory")


class APIConfig(BaseSettings):
    """API configuration for Gemini Omni video generation."""

    model_config = _ENV_CONFIG

    gemini_api_key: str = Field(
        default="",
        alias="GEMINI_API_KEY",
        description="Gemini API key, also accepts GOOGLE_API_KEY",
    )
    default_model: str = Field(default=DEFAULT_MODEL, description="Default Gemini Omni model")
    enhancement_model: str = Field(
        default=DEFAULT_ENHANCEMENT_MODEL,
        description="Text model used for optional prompt enhancement",
    )
    enable_prompt_enhancement: bool = Field(
        default=False,
        description="Enable automatic video prompt enhancement",
    )
    enable_batch_processing: bool = Field(default=True, description="Enable batch processing")
    request_timeout: int = Field(default=DEFAULT_TIMEOUT, description="Generation timeout")
    file_poll_interval: float = Field(
        default=FILE_POLL_INTERVAL,
        description="Seconds between Files API polling attempts",
    )
    file_poll_timeout: int = Field(
        default=FILE_POLL_TIMEOUT,
        description="Maximum seconds to wait for URI/file activation",
    )
    max_batch_size: int = Field(
        default=MAX_BATCH_SIZE,
        description="Maximum parallel video generations",
    )
    max_retries: int = Field(default=3, description="Maximum retries for failed requests")
    default_aspect_ratio: str = Field(
        default=DEFAULT_ASPECT_RATIO,
        description="Default video aspect ratio",
    )
    default_duration_seconds: int | None = Field(
        default=DEFAULT_DURATION_SECONDS,
        description="Optional target video duration in seconds",
    )
    default_delivery: str = Field(default=DEFAULT_DELIVERY, description="inline or uri")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GOOGLE_API_KEY", "")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required")


class Settings:
    """Combined server and API configuration."""

    def __init__(self) -> None:
        self.server = ServerConfig()
        self.api = APIConfig()
        Path(self.server.output_dir).expanduser().mkdir(parents=True, exist_ok=True)

    @property
    def output_dir(self) -> Path:
        """Output directory as a Path object."""
        return Path(self.server.output_dir).expanduser()


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the global Settings instance, creating it on first call."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
