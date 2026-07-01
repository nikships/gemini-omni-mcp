"""Batch video generation tool for multiple prompts."""

import asyncio
import base64
import json
import logging
from typing import Any

from ..config import MAX_BATCH_SIZE, get_settings
from ..core import (
    coerce_image_paths,
    validate_batch_size,
    validate_prompts_list,
    validate_reference_image,
    validate_reference_images_count,
)
from .generate_video import generate_video_tool

logger = logging.getLogger(__name__)


async def batch_generate_videos(
    prompts: list[str],
    task: str | None = None,
    aspect_ratio: str | None = None,
    duration_seconds: int | None = None,
    reference_image_paths: str | list[str] | None = None,
    batch_size: int | None = None,
    delivery: str | None = None,
    enhance_prompt: bool = False,
) -> dict[str, Any]:
    """Generate multiple videos from a list of prompts."""
    validate_prompts_list(prompts)
    reference_image_paths = coerce_image_paths(reference_image_paths)

    reference_images_data: list[dict[str, str]] | None = None
    if reference_image_paths:
        validate_reference_images_count(reference_image_paths)
        reference_images_data = []
        for img_path in reference_image_paths:
            _, image_bytes, mime_type = validate_reference_image(img_path)
            reference_images_data.append(
                {
                    "type": "image",
                    "data": base64.b64encode(image_bytes).decode(),
                    "mime_type": mime_type,
                }
            )
        if not reference_images_data:
            reference_images_data = None

    settings = get_settings()
    if batch_size is None:
        batch_size = min(settings.api.max_batch_size, MAX_BATCH_SIZE)
    validate_batch_size(batch_size, MAX_BATCH_SIZE)

    results: dict[str, Any] = {
        "success": True,
        "total_prompts": len(prompts),
        "batch_size": batch_size,
        "completed": 0,
        "failed": 0,
        "results": [],
    }

    for i in range(0, len(prompts), batch_size):
        batch = prompts[i : i + batch_size]
        logger.info("Processing video batch %s: %s prompts", i // batch_size + 1, len(batch))
        tasks = [
            generate_video_tool(
                prompt=prompt,
                task=task,
                aspect_ratio=aspect_ratio,
                duration_seconds=duration_seconds,
                reference_image_paths=None,
                reference_images_data=reference_images_data,
                delivery=delivery,
                enhance_prompt=enhance_prompt,
            )
            for prompt in batch
        ]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for j, result in enumerate(batch_results):
            prompt_index = i + j
            if isinstance(result, Exception):
                logger.error("Failed to generate video for prompt %s: %s", prompt_index, result)
                results["failed"] += 1
                results["results"].append(
                    {
                        "prompt_index": prompt_index,
                        "prompt": batch[j],
                        "success": False,
                        "error": str(result),
                    }
                )
                continue
            if not isinstance(result, dict):
                results["failed"] += 1
                results["results"].append(
                    {
                        "prompt_index": prompt_index,
                        "prompt": batch[j],
                        "success": False,
                        "error": "Unexpected result type",
                    }
                )
                continue

            results["completed"] += 1
            results["results"].append({"prompt_index": prompt_index, "prompt": batch[j], **result})

    return results


batch_generate_images = batch_generate_videos


def register_batch_generate_tool(mcp_server: Any) -> None:
    """Register batch_generate_videos with the MCP server."""

    @mcp_server.tool(timeout=1800.0)
    async def batch_generate(
        prompts: list[str],
        task: str | None = None,
        aspect_ratio: str | None = None,
        duration_seconds: int | None = None,
        reference_image_paths: str | list[str] | None = None,
        batch_size: int | None = None,
        delivery: str | None = None,
        enhance_prompt: bool = False,
    ) -> str:
        """
        Generate multiple Gemini Omni Flash videos in conservative parallel batches.

        Use for storyboards, aspect-ratio comparisons, or reference-guided variations.
        Batch size defaults to configuration and is capped at 4 because video jobs are long.
        The JSON response includes per-prompt video.path, interaction_id, metadata, and errors.
        """
        try:
            result = await batch_generate_videos(
                prompts=prompts,
                task=task,
                aspect_ratio=aspect_ratio,
                duration_seconds=duration_seconds,
                reference_image_paths=reference_image_paths,
                batch_size=batch_size,
                delivery=delivery,
                enhance_prompt=enhance_prompt,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error("Batch video generation error: %s", e)
            return json.dumps(
                {"success": False, "error": str(e), "error_type": type(e).__name__},
                indent=2,
            )
