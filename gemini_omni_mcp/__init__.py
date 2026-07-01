"""Gemini Omni MCP Server."""

__version__ = "1.0.0"
__author__ = "Gemini Omni MCP"

from .config import get_settings
from .server import create_app, main

__all__ = ["create_app", "main", "get_settings", "__version__"]
