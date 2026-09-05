#!/usr/bin/env python3
"""Gemini Omni MCP server entry point."""

import logging
import sys

from fastmcp import FastMCP

from .config import ALL_MODELS, get_settings
from .prompts import register_video_prompts
from .tools import register_batch_generate_tool, register_generate_video_tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)

SERVER_INSTRUCTIONS = """\
Generate and edit MP4 videos with Google's Gemini Omni Flash (gemini-omni-1.1-flash)
via the generate_video and batch_generate tools.

- By default Omni produces a few different shots with scene cuts; prompt
  "single continuous shot, no scene cuts" for one unbroken take, or stage your
  own cuts with timing cues ([0-3s] timecodes or "Every 2s cut to a new frame").
- Edit and extend are prompt-based: pass previous_interaction_id (or
  input_video_path for your own MP4 of 10s or less) and describe the change.
  Leave task unset for multi-turn edit/extend — the API rejects an explicit
  task together with previous_interaction_id.
- Extend appends a 3-10 second continuation per turn, up to 40s total.
- Prefer delivery="uri"; generated videos are saved to disk and returned with
  video.path — open that path with the OS video viewer after generation.
"""


def create_app() -> FastMCP:
    """Create and configure the Gemini Omni MCP application."""
    logger.info("Initializing Gemini Omni MCP Server...")
    try:
        settings = get_settings()
        logger.info("Output directory: %s", settings.output_dir)
        logger.info("Prompt enhancement: %s", settings.api.enable_prompt_enhancement)
        logger.info("Available models: %s", ", ".join(ALL_MODELS.keys()))

        mcp = FastMCP(
            "Gemini Omni MCP",
            instructions=SERVER_INSTRUCTIONS,
            version="1.0.0",
        )
        register_generate_video_tool(mcp)
        register_batch_generate_tool(mcp)
        register_video_prompts(mcp)

        logger.info("Gemini Omni MCP Server initialized successfully")
        return mcp
    except Exception as e:
        logger.error("Failed to initialize server: %s", e, exc_info=True)
        raise


def main() -> None:
    """Main entry point for direct execution."""
    try:
        logger.info("Starting Gemini Omni MCP Server...")
        app = create_app()
        logger.info("Server is ready and listening for MCP requests")
        app.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Server error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
