"""Constants for the Gemini Omni MCP server."""

from pathlib import Path

OMNI_MODELS = {
    "gemini-omni-1.1-flash": "gemini-omni-1.1-flash",
    "gemini-flash-latest": "gemini-flash-latest",
}

GEMINI_MODELS = OMNI_MODELS
ALL_MODELS = OMNI_MODELS

DEFAULT_MODEL = "gemini-omni-1.1-flash"
DEFAULT_ENHANCEMENT_MODEL = "gemini-flash-latest"

VIDEO_ASPECT_RATIOS = ["16:9", "9:16"]
DEFAULT_ASPECT_RATIO = "16:9"

VIDEO_RESOLUTIONS = ["360p", "720p", "1080p", "4k"]
DEFAULT_RESOLUTION = "720p"

OMNI_TASKS = ["text_to_video", "image_to_video", "reference_to_video", "edit", "extend"]
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
