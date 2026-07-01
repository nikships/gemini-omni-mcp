"""Tools module for Gemini Omni MCP."""

from .batch_generate import batch_generate_videos, register_batch_generate_tool
from .generate_video import generate_video_tool, register_generate_video_tool

__all__ = [
    "generate_video_tool",
    "register_generate_video_tool",
    "batch_generate_videos",
    "register_batch_generate_tool",
]
