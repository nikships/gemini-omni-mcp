"""Constants for the Gemini Omni MCP server."""

from pathlib import Path

OMNI_MODELS = {
    "gemini-omni-flash-preview": "gemini-omni-flash-preview",
    "gemini-flash-latest": "gemini-flash-latest",
}

GEMINI_MODELS = OMNI_MODELS
ALL_MODELS = OMNI_MODELS

DEFAULT_MODEL = "gemini-omni-flash-preview"
DEFAULT_ENHANCEMENT_MODEL = "gemini-flash-latest"

VIDEO_ASPECT_RATIOS = ["16:9", "9:16"]
DEFAULT_ASPECT_RATIO = "16:9"

OMNI_TASKS = ["text_to_video", "image_to_video", "reference_to_video", "edit"]
DELIVERY_OPTIONS = ["inline", "uri"]
DEFAULT_DELIVERY = "uri"

VIDEO_MIME_TYPE = "video/mp4"
VIDEO_EXTENSIONS = {".mp4": VIDEO_MIME_TYPE}

IMAGE_MIME_TYPES = {
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}

MIN_DURATION_SECONDS = 3
MAX_DURATION_SECONDS = 10
DEFAULT_DURATION_SECONDS: int | None = None

MAX_REFERENCE_IMAGES = 6
MAX_PROMPT_LENGTH = 8192

MAX_IMAGE_SIZE_MB = 20
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
MAX_INPUT_VIDEO_SIZE_MB = 2048
MAX_INPUT_VIDEO_SIZE_BYTES = MAX_INPUT_VIDEO_SIZE_MB * 1024 * 1024

MAX_BATCH_SIZE = 4
DEFAULT_TIMEOUT = 300
FILE_POLL_INTERVAL = 5.0
FILE_POLL_TIMEOUT = 600

DEFAULT_OUTPUT_DIR = str(Path.home() / "gemini_omni_videos")
