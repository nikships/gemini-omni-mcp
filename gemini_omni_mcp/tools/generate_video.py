"""MCP tool for Gemini Omni Flash video generation and editing."""

import base64
import functools
import json
import logging
from pathlib import Path
from typing import Any

from ..config import get_settings
from ..core import (
    ValidationError,
    coerce_image_paths,
    validate_delivery,
    validate_duration_seconds,
    validate_input_video,
    validate_prompt,
    validate_reference_image,
    validate_reference_images_count,
    validate_task,
    validate_video_aspect_ratio,
)
from ..services import VideoService

logger = logging.getLogger(__name__)


@functools.lru_cache
def get_video_service(
    api_key: str,
    enable_enhancement: bool,
    timeout: int,
    file_poll_interval: float,
    file_poll_timeout: int,
) -> VideoService:
    """Get or create a cached VideoService instance."""
    return VideoService(
        api_key=api_key,
        enable_enhancement=enable_enhancement,
        timeout=timeout,
        file_poll_interval=file_poll_interval,
        file_poll_timeout=file_poll_timeout,
    )


async def generate_video_tool(
    prompt: str,
    task: str | None = None,
    aspect_ratio: str | None = None,
    duration_seconds: int | None = None,
    reference_image_paths: str | list[str] | None = None,
    reference_images_data: list[dict[str, str]] | None = None,
    input_video_path: str | None = None,
    delivery: str | None = None,
    previous_interaction_id: str | None = None,
    save_to_disk: bool = True,
    enhance_prompt: bool = False,
) -> dict[str, Any]:
    """Generate or edit a video with Gemini Omni Flash."""
    reference_image_paths = coerce_image_paths(reference_image_paths)

    settings = get_settings()
    validate_prompt(prompt)
    task = validate_task(task)
    aspect_ratio = validate_video_aspect_ratio(aspect_ratio or settings.api.default_aspect_ratio)
    duration_seconds = validate_duration_seconds(
        duration_seconds if duration_seconds is not None else settings.api.default_duration_seconds
    )
    delivery = validate_delivery(delivery or settings.api.default_delivery)

    if reference_image_paths:
        validate_reference_images_count(reference_image_paths)

    model = settings.api.default_model
    video_service = get_video_service(
        api_key=settings.api.gemini_api_key,
        enable_enhancement=settings.api.enable_prompt_enhancement or enhance_prompt,
        timeout=settings.api.request_timeout,
        file_poll_interval=settings.api.file_poll_interval,
        file_poll_timeout=settings.api.file_poll_timeout,
    )

    reference_images = reference_images_data[:] if reference_images_data else []
    if reference_image_paths:
        for img_path in reference_image_paths:
            _, image_bytes, mime_type = validate_reference_image(img_path)
            reference_images.append(
                {
                    "type": "image",
                    "data": base64.b64encode(image_bytes).decode(),
                    "mime_type": mime_type,
                }
            )

    uploaded_video_uri: str | None = None
    uploaded_video_path: Path | None = None
    if input_video_path:
        uploaded_video_path = validate_input_video(input_video_path)
        uploaded_video_uri = await video_service.upload_video(uploaded_video_path)
        if task is None:
            task = "edit"

    if task is None:
        if previous_interaction_id or uploaded_video_uri:
            task = "edit"
        elif reference_images:
            task = "reference_to_video" if len(reference_images) > 1 else "image_to_video"
        else:
            task = "text_to_video"

    if task == "edit" and not (previous_interaction_id or uploaded_video_uri):
        raise ValidationError("edit task requires previous_interaction_id or input_video_path")
    if task == "image_to_video" and len(reference_images) != 1:
        raise ValidationError("image_to_video task requires exactly one reference image")
    if task == "reference_to_video" and not reference_images:
        raise ValidationError("reference_to_video task requires at least one reference image")

    result = await video_service.generate(
        prompt=prompt,
        model=model,
        enhance_prompt=settings.api.enable_prompt_enhancement or enhance_prompt,
        task=task,
        reference_images=reference_images or None,
        uploaded_video_uri=uploaded_video_uri,
        aspect_ratio=aspect_ratio,
        duration_seconds=duration_seconds,
        delivery=delivery,
        previous_interaction_id=previous_interaction_id,
    )

    video_info: dict[str, Any] = {
        "size": result.get_size(),
        "timestamp": result.timestamp.isoformat(),
        "mime_type": result.mime_type,
    }
    if save_to_disk:
        file_path = result.save(settings.output_dir)
        video_info["path"] = str(file_path)
        video_info["filename"] = file_path.name

    response: dict[str, Any] = {
        "success": True,
        "model": model,
        "prompt": prompt,
        "interaction_id": result.interaction_id,
        "video": video_info,
        "metadata": {
            "task": task,
            "aspect_ratio": aspect_ratio,
            "duration_seconds": duration_seconds,
            "delivery": delivery,
            "reference_images": len(reference_images),
            "input_video_path": str(uploaded_video_path) if uploaded_video_path else None,
            "uploaded_video_uri": uploaded_video_uri,
            "previous_interaction_id": previous_interaction_id,
            "enhanced_prompt": result.metadata.get("enhanced_prompt"),
            "uri": result.metadata.get("uri"),
        },
    }
    response["metadata"] = {k: v for k, v in response["metadata"].items() if v is not None}
    return response


def register_generate_video_tool(mcp_server: Any) -> None:
    """Register the generate_video MCP tool."""

    @mcp_server.tool(timeout=900.0)
    async def generate_video(
        prompt: str,
        task: str | None = None,
        aspect_ratio: str | None = None,
        duration_seconds: int | None = None,
        reference_image_paths: str | list[str] | None = None,
        input_video_path: str | None = None,
        delivery: str | None = None,
        previous_interaction_id: str | None = None,
        enhance_prompt: bool = False,
    ) -> str:
        """
        Generate or edit MP4 videos with Gemini Omni Flash.

        Capabilities:
        - text_to_video: prompt-only video with generated audio.
        - image_to_video: one reference image plus motion and camera direction.
        - reference_to_video: multiple reference images for subjects, style, or props.
        - edit: use previous_interaction_id or input_video_path to edit existing video.

        Parameters:
        - prompt: Describe the scene, motion, camera movement, lighting, mood, and audio.
        - task: text_to_video, image_to_video, reference_to_video, or edit. If omitted, inferred.
        - aspect_ratio: 16:9 landscape or 9:16 portrait.
        - duration_seconds: Optional 3 to 10 second target. If the API rejects this preview field, retry without it.
        - reference_image_paths: Up to 6 local images. Use <FIRST_FRAME> or <IMAGE_REF_N> tags in the prompt for control.
        - input_video_path: Local MP4 to upload and edit through the Files API.
        - delivery: uri is recommended for generated MP4 files; inline is supported for smaller payloads.
        - previous_interaction_id: Continue editing a prior generated video.
        - enhance_prompt: Optional, default false. For edits, simple prompts usually work better.

        Prompt tips:
        - Ask for "single continuous shot" and "no scene cuts" when you want one scene.
        - Include explicit audio direction such as "gentle ambient room tone, no dialogue".
        - For edits, say "Keep everything else the same".
        - Timing cues like [0-3s], [3-6s], [6-10s] are supported.

        Limitations:
        - Output is MP4, currently 720p at 24fps, SynthID-watermarked, and preview quality.
        - System instructions, temperature, top_p, stop sequences, negative_prompt, voice edits, YouTube sources, and multi-video reasoning are unsupported.
        - Uploaded-video editing is unavailable in some regions.

        Returns JSON including video.path, interaction_id, task, aspect_ratio, delivery, size, and URI metadata.
        After success, open video.path with the native OS video viewer.
        """
        try:
            result = await generate_video_tool(
                prompt=prompt,
                task=task,
                aspect_ratio=aspect_ratio,
                duration_seconds=duration_seconds,
                reference_image_paths=reference_image_paths,
                input_video_path=input_video_path,
                delivery=delivery,
                previous_interaction_id=previous_interaction_id,
                enhance_prompt=enhance_prompt,
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error("Error generating video: %s", e)
            return json.dumps(
                {"success": False, "error": str(e), "error_type": type(e).__name__},
                indent=2,
            )
