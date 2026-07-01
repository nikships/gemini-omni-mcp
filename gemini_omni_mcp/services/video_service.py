"""Video service for Gemini Omni Flash generation and editing."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..config.constants import DEFAULT_MODEL, OMNI_MODELS, VIDEO_MIME_TYPE
from ..core.exceptions import VideoProcessingError
from .gemini_client import GeminiVideoClient
from .prompt_enhancer import PromptEnhancer

logger = logging.getLogger(__name__)


class VideoResult:
    """Container for a generated video and its metadata."""

    def __init__(
        self,
        video_bytes: bytes,
        prompt: str,
        model: str,
        *,
        interaction_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        mime_type: str = VIDEO_MIME_TYPE,
    ) -> None:
        self.video_bytes = video_bytes
        self.prompt = prompt
        self.model = model
        self.interaction_id = interaction_id
        self.metadata = metadata or {}
        self.mime_type = mime_type
        self.timestamp = datetime.now()

    def save(self, output_dir: Path, filename: str | None = None) -> Path:
        """Save the video to disk and return the output path."""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / (filename or self._generate_filename())
        try:
            output_path.write_bytes(self.video_bytes)
            logger.info("Saved video to %s", output_path)
            return output_path
        except Exception as e:
            raise VideoProcessingError(f"Failed to save video: {e}") from e

    def _generate_filename(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.prompt[:60].lower()).strip("-") or "video"
        time_suffix = self.timestamp.strftime("%H%M%S")
        uuid_prefix = str(uuid4())[:8]
        return f"{slug}-{time_suffix}-{self.timestamp.microsecond:06d}-{uuid_prefix}.mp4"

    def get_size(self) -> int:
        """Return the video size in bytes."""
        return len(self.video_bytes)


class VideoService:
    """Orchestrates Gemini Omni Flash video generation."""

    def __init__(
        self,
        api_key: str,
        *,
        enable_enhancement: bool = False,
        timeout: int = 300,
        file_poll_interval: float = 5.0,
        file_poll_timeout: int = 600,
    ) -> None:
        self.enable_enhancement = enable_enhancement
        self.gemini_client = GeminiVideoClient(
            api_key=api_key,
            timeout=timeout,
            file_poll_interval=file_poll_interval,
            file_poll_timeout=file_poll_timeout,
        )
        self.prompt_enhancer: PromptEnhancer | None = (
            PromptEnhancer(self.gemini_client) if enable_enhancement else None
        )

    async def upload_video(self, path: Path) -> str:
        """Upload a video with the Files API and return its Gemini URI."""
        return await self.gemini_client.upload_video(path)

    async def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        enhance_prompt: bool = False,
        **kwargs: Any,
    ) -> VideoResult:
        """Generate or edit a video using Gemini Omni Flash."""
        if model is None:
            model = DEFAULT_MODEL
        if model not in OMNI_MODELS:
            raise ValueError(f"Unknown model: {model}. Supported: {', '.join(OMNI_MODELS.keys())}")

        original_prompt = prompt
        if enhance_prompt and self.prompt_enhancer:
            try:
                result = await self.prompt_enhancer.enhance_prompt(
                    prompt,
                    context=self._build_enhancement_context(kwargs),
                )
                prompt = result["enhanced_prompt"]
                logger.info("Prompt enhanced: %s -> %s chars", len(original_prompt), len(prompt))
            except Exception as e:
                logger.warning("Prompt enhancement failed, using original: %s", e)

        response = await self.gemini_client.generate_video(prompt=prompt, model=model, **kwargs)
        video_bytes = response.get("video_bytes")
        if not isinstance(video_bytes, bytes):
            raise VideoProcessingError("Gemini Omni response did not contain video bytes")

        metadata = {
            "enhanced_prompt": prompt,
            **kwargs,
            "uri": response.get("uri"),
            "data_b64": response.get("data_b64"),
            "delivery": response.get("delivery"),
            "task": response.get("task"),
            "aspect_ratio": response.get("aspect_ratio"),
            "duration_seconds": response.get("duration_seconds"),
        }
        return VideoResult(
            video_bytes=video_bytes,
            prompt=original_prompt,
            model=model,
            interaction_id=response.get("interaction_id"),
            metadata={k: v for k, v in metadata.items() if v is not None},
            mime_type=str(response.get("mime_type") or VIDEO_MIME_TYPE),
        )

    def _build_enhancement_context(self, params: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = {}
        if params.get("reference_images"):
            context["has_reference_images"] = True
            context["num_reference_images"] = len(params["reference_images"])
        if params.get("uploaded_video_uri") or params.get("previous_interaction_id"):
            context["is_editing"] = True
        if "aspect_ratio" in params:
            context["aspect_ratio"] = params["aspect_ratio"]
        return context

    async def close(self) -> None:
        """Close the underlying Gemini client."""
        await self.gemini_client.close()
