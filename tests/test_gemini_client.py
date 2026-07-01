from types import SimpleNamespace
from typing import Any

import pytest

from gemini_omni_mcp.core.exceptions import APIError
from gemini_omni_mcp.services.gemini_client import GeminiVideoClient


class State:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeInteractions:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    async def create(self, **body: Any) -> Any:
        self.calls.append(body)
        return self.response


class FakeFiles:
    def __init__(self, states: list[str] | None = None, download_bytes: bytes = b"video") -> None:
        self.states = states or ["ACTIVE"]
        self.download_bytes = download_bytes
        self.get_calls: list[str] = []
        self.download_calls: list[Any] = []
        self.upload_calls: list[Any] = []

    async def get(self, *, name: str, config: Any = None) -> Any:
        self.get_calls.append(name)
        state = self.states.pop(0) if self.states else "ACTIVE"
        return SimpleNamespace(name=name, state=State(state), uri=f"https://example.com/{name}")

    async def download(self, *, file: Any, config: Any = None) -> bytes:
        self.download_calls.append(file)
        return self.download_bytes

    async def upload(self, *, file: Any, config: Any = None) -> Any:
        self.upload_calls.append(file)
        return SimpleNamespace(
            name="files/uploaded", state=State("PROCESSING"), uri="files/uploaded"
        )


class FakeClient:
    def __init__(self, interactions: FakeInteractions, files: FakeFiles) -> None:
        self.aio = SimpleNamespace(interactions=interactions, files=files, models=SimpleNamespace())


def patch_client(
    monkeypatch: pytest.MonkeyPatch, response: Any, files: FakeFiles | None = None
) -> tuple[FakeInteractions, FakeFiles]:
    interactions = FakeInteractions(response)
    fake_files = files or FakeFiles()
    fake_client = FakeClient(interactions, fake_files)
    monkeypatch.setattr(
        "gemini_omni_mcp.services.gemini_client.genai.Client", lambda api_key: fake_client
    )
    return interactions, fake_files


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_video_inline_output(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(
        id="v1_inline",
        output_video=SimpleNamespace(data="dmlkZW8=", mime_type="video/mp4"),
        steps=[],
    )
    interactions, _ = patch_client(monkeypatch, response)
    client = GeminiVideoClient("key", file_poll_interval=0)

    result = await client.generate_video(
        "A marble rolls.",
        task="text_to_video",
        aspect_ratio="16:9",
        delivery="inline",
    )

    assert result["video_bytes"] == b"video"
    assert result["interaction_id"] == "v1_inline"
    call = interactions.calls[0]
    assert call["model"] == "gemini-omni-flash-preview"
    assert call["input"] == "A marble rolls."
    assert call["response_format"] == {
        "type": "video",
        "aspect_ratio": "16:9",
        "delivery": "inline",
    }
    assert call["generation_config"] == {"video_config": {"task": "text_to_video"}}
    assert call["store"] is True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_video_uri_output_polls_and_downloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = SimpleNamespace(
        id="v1_uri",
        output_video=SimpleNamespace(
            uri="https://generativelanguage.googleapis.com/v1beta/files/abc123:download?alt=media",
            mime_type="video/mp4",
        ),
        steps=[],
    )
    files = FakeFiles(states=["PROCESSING", "ACTIVE"], download_bytes=b"downloaded")
    _, fake_files = patch_client(monkeypatch, response, files)
    client = GeminiVideoClient("key", file_poll_interval=0, file_poll_timeout=5)

    result = await client.generate_video("A sunset.", delivery="uri")

    assert result["video_bytes"] == b"downloaded"
    assert fake_files.get_calls == ["files/abc123", "files/abc123"]
    assert fake_files.download_calls == [
        "https://generativelanguage.googleapis.com/v1beta/files/abc123:download?alt=media"
    ]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_video_failed_uri_state(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(
        id="v1_uri",
        output_video=SimpleNamespace(uri="files/bad", mime_type="video/mp4"),
        steps=[],
    )
    patch_client(monkeypatch, response, FakeFiles(states=["FAILED"]))
    client = GeminiVideoClient("key", file_poll_interval=0)

    with pytest.raises(APIError, match="File processing failed"):
        await client.generate_video("A sunset.", delivery="uri")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_steps_fallback_and_previous_interaction_id(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(
        id="v1_steps",
        output_video=None,
        steps=[
            SimpleNamespace(type="user_input", content=[]),
            SimpleNamespace(
                type="model_output",
                content=[{"type": "video", "mime_type": "video/mp4", "data": "c3RlcHM="}],
            ),
        ],
    )
    interactions, _ = patch_client(monkeypatch, response)
    client = GeminiVideoClient("key")

    result = await client.generate_video(
        "Make the sky purple. Keep everything else the same.",
        previous_interaction_id="v1_previous",
        task="edit",
    )

    assert result["video_bytes"] == b"steps"
    assert interactions.calls[0]["previous_interaction_id"] == "v1_previous"
    assert "generation_config" not in interactions.calls[0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reference_images_and_duration_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(
        id="v1_ref",
        output_video=SimpleNamespace(data="cmVm", mime_type="video/mp4"),
        steps=[],
    )
    interactions, _ = patch_client(monkeypatch, response)
    client = GeminiVideoClient("key")

    await client.generate_video(
        "Animate <IMAGE_REF_0> with <IMAGE_REF_1>.",
        task="reference_to_video",
        reference_images=[
            {"type": "image", "data": "a", "mime_type": "image/jpeg"},
            {"type": "image", "data": "b", "mime_type": "image/png"},
        ],
        duration_seconds=10,
    )

    call = interactions.calls[0]
    assert call["input"] == [
        {"type": "image", "data": "a", "mime_type": "image/jpeg"},
        {"type": "image", "data": "b", "mime_type": "image/png"},
        {"type": "text", "text": "Animate <IMAGE_REF_0> with <IMAGE_REF_1>."},
    ]
    assert call["response_format"]["duration"] == "10s"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_video_waits_for_active(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    response = SimpleNamespace(id="unused", output_video=None, steps=[])
    files = FakeFiles(states=["PROCESSING", "ACTIVE"])
    _, fake_files = patch_client(monkeypatch, response, files)
    client = GeminiVideoClient("key", file_poll_interval=0)
    video = tmp_path / "input.mp4"
    video.write_bytes(b"video")

    uri = await client.upload_video(video)

    assert uri == "https://example.com/files/uploaded"
    assert fake_files.upload_calls == [video]
    assert fake_files.get_calls == ["files/uploaded", "files/uploaded"]
