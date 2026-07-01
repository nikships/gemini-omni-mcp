"""Input validation utilities."""

import base64
import io
import json
import re
from pathlib import Path

from PIL import Image

from ..config.constants import (
    ALL_MODELS,
    DELIVERY_OPTIONS,
    IMAGE_MIME_TYPES,
    MAX_DURATION_SECONDS,
    MAX_IMAGE_SIZE_BYTES,
    MAX_INPUT_VIDEO_SIZE_BYTES,
    MAX_PROMPT_LENGTH,
    MAX_REFERENCE_IMAGES,
    MIN_DURATION_SECONDS,
    OMNI_TASKS,
    VIDEO_ASPECT_RATIOS,
    VIDEO_EXTENSIONS,
)
from .exceptions import ValidationError


def validate_prompt(prompt: str) -> None:
    """Validate prompt text."""
    if not prompt or not prompt.strip():
        raise ValidationError("Prompt cannot be empty")
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise ValidationError(
            f"Prompt too long: {len(prompt)} characters (max {MAX_PROMPT_LENGTH})"
        )


def validate_model(model: str) -> None:
    """Validate model name."""
    if model not in ALL_MODELS:
        available = ", ".join(ALL_MODELS.keys())
        raise ValidationError(f"Invalid model '{model}'. Available models: {available}")


def validate_video_aspect_ratio(aspect_ratio: str) -> str:
    """Validate and return a Gemini Omni video aspect ratio."""
    if aspect_ratio not in VIDEO_ASPECT_RATIOS:
        available = ", ".join(VIDEO_ASPECT_RATIOS)
        raise ValidationError(f"Invalid aspect ratio '{aspect_ratio}'. Available: {available}")
    return aspect_ratio


def validate_task(task: str | None) -> str | None:
    """Validate and return an optional Omni video task."""
    if task is None or task == "":
        return None
    if task not in OMNI_TASKS:
        available = ", ".join(OMNI_TASKS)
        raise ValidationError(f"Invalid task '{task}'. Available: {available}")
    return task


def validate_duration_seconds(duration_seconds: int | None) -> int | None:
    """Validate and return an optional target video duration."""
    if duration_seconds is None:
        return None
    if not isinstance(duration_seconds, int):
        raise ValidationError("duration_seconds must be an integer")
    if duration_seconds < MIN_DURATION_SECONDS or duration_seconds > MAX_DURATION_SECONDS:
        raise ValidationError(
            f"duration_seconds must be between {MIN_DURATION_SECONDS} and "
            f"{MAX_DURATION_SECONDS}, got {duration_seconds}"
        )
    return duration_seconds


def validate_delivery(delivery: str) -> str:
    """Validate video delivery mode."""
    if delivery not in DELIVERY_OPTIONS:
        available = ", ".join(DELIVERY_OPTIONS)
        raise ValidationError(f"Invalid delivery '{delivery}'. Available: {available}")
    return delivery


def validate_file_path(path: str) -> Path:
    """Validate that the path exists and refers to a file."""
    try:
        file_path = Path(path).expanduser().resolve()
    except Exception as e:
        raise ValidationError(f"Invalid file path '{path}': {e}") from e

    if not file_path.exists():
        raise ValidationError(f"File does not exist: {file_path}")
    if not file_path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")

    return file_path


def detect_image_mime_type(path: Path, image_bytes: bytes) -> str:
    """Detect an image MIME type using Pillow metadata and extension fallback."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            image_format = (img.format or "").lower()
            img.verify()
    except Exception as e:
        raise ValidationError(f"Invalid image file {path}: {e}") from e

    if image_format in IMAGE_MIME_TYPES:
        return IMAGE_MIME_TYPES[image_format]

    extension = path.suffix.lower().lstrip(".")
    if extension in IMAGE_MIME_TYPES:
        return IMAGE_MIME_TYPES[extension]

    available = ", ".join(sorted(IMAGE_MIME_TYPES))
    raise ValidationError(f"Unsupported image format for {path}. Available: {available}")


def validate_reference_image(path: str | Path) -> tuple[Path, bytes, str]:
    """Validate a reference image and return path, bytes, and MIME type."""
    file_path = validate_file_path(str(path))
    file_size = file_path.stat().st_size
    if file_size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Reference image too large: {file_size / (1024 * 1024):.1f}MB "
            f"(max {MAX_IMAGE_SIZE_BYTES / (1024 * 1024):.0f}MB): {file_path}"
        )
    if file_size == 0:
        raise ValidationError(f"Reference image is empty: {file_path}")

    image_bytes = file_path.read_bytes()
    mime_type = detect_image_mime_type(file_path, image_bytes)
    return file_path, image_bytes, mime_type


def validate_input_video(path: str | Path) -> Path:
    """Validate an uploaded input video path for editing."""
    file_path = validate_file_path(str(path))
    if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
        available = ", ".join(VIDEO_EXTENSIONS.keys())
        raise ValidationError(
            f"Unsupported input video format '{file_path.suffix}'. Use: {available}"
        )
    file_size = file_path.stat().st_size
    if file_size == 0:
        raise ValidationError(f"Input video is empty: {file_path}")
    if file_size > MAX_INPUT_VIDEO_SIZE_BYTES:
        raise ValidationError(
            f"Input video too large: {file_size / (1024 * 1024):.1f}MB "
            f"(max {MAX_INPUT_VIDEO_SIZE_BYTES / (1024 * 1024):.0f}MB): {file_path}"
        )
    return file_path


def coerce_image_paths(value: str | list[str] | None) -> list[str] | None:
    """Normalize a reference-image-paths argument into a list of paths."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                return [stripped]
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
            return [str(parsed)]
        return [stripped]
    return list(value)


def validate_reference_images_count(image_paths: list[str]) -> None:
    """Validate the number of reference images does not exceed the maximum."""
    if len(image_paths) > MAX_REFERENCE_IMAGES:
        raise ValidationError(
            f"Too many reference images: {len(image_paths)} (max {MAX_REFERENCE_IMAGES})"
        )


def validate_base64_image(data: str) -> None:
    """Validate base64-encoded image data."""
    if not data:
        raise ValidationError("Base64 image data cannot be empty")
    try:
        decoded = base64.b64decode(data, validate=True)
    except Exception as e:
        raise ValidationError(f"Invalid base64 image data: {e}") from e
    if len(decoded) == 0:
        raise ValidationError("Decoded image data is empty")


def validate_prompts_list(prompts: list[str]) -> None:
    """Validate a list of prompts for batch processing."""
    if not isinstance(prompts, list):
        raise ValidationError("Prompts must be a list")
    if not prompts:
        raise ValidationError("Prompts list cannot be empty")

    for i, prompt in enumerate(prompts):
        if not isinstance(prompt, str):
            raise ValidationError(f"Prompt at index {i} must be a string")
        try:
            validate_prompt(prompt)
        except ValidationError as e:
            raise ValidationError(f"Invalid prompt at index {i}: {e}") from e


def validate_batch_size(size: int, max_size: int) -> None:
    """Validate a positive integer batch size within the allowed maximum."""
    if not isinstance(size, int) or size < 1:
        raise ValidationError(f"Batch size must be at least 1, got {size}")
    if size > max_size:
        raise ValidationError(f"Batch size exceeds maximum: {size} > {max_size}")


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by replacing special characters with underscores."""
    safe_name = re.sub(r"[^a-zA-Z0-9-]", "_", filename)
    safe_name = re.sub(r"_+", "_", safe_name)
    safe_name = safe_name.strip("_")
    return safe_name or "video"
