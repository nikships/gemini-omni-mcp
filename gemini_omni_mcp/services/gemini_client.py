"""Gemini Omni client using the official Google GenAI SDK."""

import asyncio
import base64
import logging
import re
import time
from pathlib import Path
from typing import Any

from google import genai

from ..config.constants import (
    DEFAULT_DELIVERY,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    FILE_POLL_INTERVAL,
    FILE_POLL_TIMEOUT,
    GEMINI_MODELS,
    VIDEO_MIME_TYPE,
)
from ..core.exceptions import APIError, AuthenticationError, ContentPolicyError, RateLimitError

logger = logging.getLogger(__name__)


class GeminiVideoClient:
    """Client for Gemini Omni Flash video generation and editing."""

    def __init__(
        self,
        api_key: str,
        timeout: int = DEFAULT_TIMEOUT,
        *,
        file_poll_interval: float = FILE_POLL_INTERVAL,
        file_poll_timeout: int = FILE_POLL_TIMEOUT,
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.file_poll_interval = file_poll_interval
        self.file_poll_timeout = file_poll_timeout
        self.client = genai.Client(api_key=api_key)

    async def generate_video(
        self,
        prompt: str,
        *,
        model: str = DEFAULT_MODEL,
        task: str | None = None,
        reference_images: list[dict[str, str]] | None = None,
        uploaded_video_uri: str | None = None,
        aspect_ratio: str = "16:9",
        duration_seconds: int | None = None,
        delivery: str = DEFAULT_DELIVERY,
        previous_interaction_id: str | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Generate or edit a video with Gemini Omni Flash."""
        model_id = GEMINI_MODELS.get(model, model)
        request_timeout = timeout or self.timeout

        try:
            interaction_input = self._build_input(
                prompt=prompt,
                reference_images=reference_images,
                uploaded_video_uri=uploaded_video_uri,
            )
            response_format: dict[str, Any] = {
                "type": "video",
                "aspect_ratio": aspect_ratio,
                "delivery": delivery,
            }
            if duration_seconds is not None:
                response_format["duration"] = f"{duration_seconds}s"

            body: dict[str, Any] = {
                "model": model_id,
                "input": interaction_input,
                "response_format": response_format,
                "store": True,
            }
            if task and task != "edit":
                body["generation_config"] = {"video_config": {"task": task}}
            if previous_interaction_id:
                body["previous_interaction_id"] = previous_interaction_id

            logger.info(
                "Generating video: model=%s task=%s aspect_ratio=%s delivery=%s references=%s",
                model_id,
                task,
                aspect_ratio,
                delivery,
                len(reference_images or []),
            )

            interaction = await self.client.aio.interactions.create(
                timeout=request_timeout,
                **body,
            )
            output = self._extract_video_output(interaction)

            if output.get("uri") and not output.get("video_bytes"):
                output["video_bytes"] = await self._download_uri_video(str(output["uri"]))

            if output.get("data_b64") and not output.get("video_bytes"):
                output["video_bytes"] = base64.b64decode(str(output["data_b64"]))

            if not output.get("video_bytes"):
                raise APIError("No video data found in Gemini Omni API response")

            output.update(
                {
                    "interaction_id": getattr(interaction, "id", None),
                    "model": model,
                    "task": task,
                    "aspect_ratio": aspect_ratio,
                    "duration_seconds": duration_seconds,
                    "delivery": delivery,
                }
            )
            return output
        except Exception as e:
            logger.error("Gemini Omni API request failed: %s", e)
            self._handle_exception(e)
            raise APIError(f"Gemini Omni API request failed: {e}") from e

    async def upload_video(self, path: Path) -> str:
        """Upload a video with the Files API and return its Gemini URI."""
        try:
            video_file = await self.client.aio.files.upload(file=path)
            video_file = await self._wait_for_file_active(video_file)
            uri = getattr(video_file, "uri", None)
            if not uri:
                raise APIError("Uploaded file did not return a URI")
            return str(uri)
        except Exception as e:
            logger.error("Gemini file upload failed: %s", e)
            self._handle_exception(e)
            raise APIError(f"Gemini file upload failed: {e}") from e

    async def generate_text(
        self,
        prompt: str,
        *,
        model: str = "gemini-flash-latest",
        system_instruction: str | None = None,
    ) -> str:
        """Generate text using Gemini for optional prompt enhancement."""
        model_id = GEMINI_MODELS.get(model, model)
        try:
            config: Any = {"system_instruction": system_instruction} if system_instruction else None
            response = await self.client.aio.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config,
            )
            return getattr(response, "text", "") or ""
        except Exception as e:
            logger.error("Gemini text generation failed: %s", e)
            raise APIError(f"Gemini text generation failed: {e}") from e

    def _build_input(
        self,
        *,
        prompt: str,
        reference_images: list[dict[str, str]] | None,
        uploaded_video_uri: str | None,
    ) -> str | list[dict[str, str]]:
        if not reference_images and not uploaded_video_uri:
            return prompt

        parts: list[dict[str, str]] = []
        if uploaded_video_uri:
            parts.append({"type": "document", "uri": uploaded_video_uri})
        if reference_images:
            parts.extend(reference_images)
        parts.append({"type": "text", "text": prompt})
        return parts

    def _extract_video_output(self, interaction: Any) -> dict[str, Any]:
        """Extract video output from SDK convenience field or steps fallback."""
        output_video = getattr(interaction, "output_video", None)
        if output_video is not None:
            extracted = self._extract_video_content(output_video)
            if extracted:
                return extracted

        steps = getattr(interaction, "steps", None) or []
        for step in steps:
            if self._get_value(step, "type") != "model_output":
                continue
            for content in self._get_value(step, "content") or []:
                if self._get_value(content, "type") == "video":
                    extracted = self._extract_video_content(content)
                    if extracted:
                        return extracted

        return {}

    def _extract_video_content(self, content: Any) -> dict[str, Any]:
        data_b64 = self._get_value(content, "data")
        uri = self._get_value(content, "uri")
        mime_type = self._get_value(content, "mime_type") or VIDEO_MIME_TYPE
        result: dict[str, Any] = {"mime_type": mime_type}
        if data_b64:
            result["data_b64"] = data_b64
        if uri:
            result["uri"] = uri
        return result if data_b64 or uri else {}

    async def _download_uri_video(self, uri: str) -> bytes:
        file_id = self._extract_file_id(uri)
        await self._wait_for_file_name_active(f"files/{file_id}")
        video_bytes = await self.client.aio.files.download(file=uri)
        if not isinstance(video_bytes, bytes):
            raise APIError("Files API download did not return bytes")
        return video_bytes

    async def _wait_for_file_active(self, file_obj: Any) -> Any:
        name = getattr(file_obj, "name", None)
        if not name:
            return file_obj
        return await self._wait_for_file_name_active(str(name), initial_file=file_obj)

    async def _wait_for_file_name_active(self, name: str, initial_file: Any | None = None) -> Any:
        deadline = time.monotonic() + self.file_poll_timeout
        file_obj = initial_file
        while True:
            if file_obj is None:
                file_obj = await self.client.aio.files.get(name=name)

            state = self._state_name(getattr(file_obj, "state", None))
            if state == "ACTIVE":
                return file_obj
            if state == "FAILED":
                raise APIError(f"File processing failed for {name}")
            if time.monotonic() >= deadline:
                raise APIError(f"Timed out waiting for file to become ACTIVE: {name}")

            await asyncio.sleep(self.file_poll_interval)
            file_obj = await self.client.aio.files.get(name=name)

    def _extract_file_id(self, uri: str) -> str:
        match = re.search(r"files/([^/:?]+)", uri)
        if match:
            return match.group(1)
        tail = uri.rstrip("/").split("/")[-1]
        return tail.split(":", 1)[0]

    def _state_name(self, state: Any) -> str:
        if state is None:
            return ""
        return str(getattr(state, "name", state)).upper()

    def _get_value(self, obj: Any, key: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    def _handle_exception(self, error: Exception) -> None:
        """Categorize and re-raise SDK exceptions as typed errors."""
        error_msg = str(error).lower()
        if "authentication" in error_msg or "api key" in error_msg or "unauthorized" in error_msg:
            raise AuthenticationError("Authentication failed. Please check your Gemini API key.")
        if "rate limit" in error_msg or "quota" in error_msg or "resource_exhausted" in error_msg:
            raise RateLimitError("Rate limit exceeded. Please try again later.")
        if "safety" in error_msg or "blocked" in error_msg or "policy" in error_msg:
            raise ContentPolicyError("Content was blocked by safety filters. Modify your prompt.")

    async def close(self) -> None:
        """No-op: the GenAI SDK handles cleanup automatically."""


GeminiClient = GeminiVideoClient
