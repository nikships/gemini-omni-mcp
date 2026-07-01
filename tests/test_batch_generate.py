from pathlib import Path
from typing import Any

import pytest

from gemini_omni_mcp.tools import batch_generate as batch_module


@pytest.mark.asyncio
@pytest.mark.integration
async def test_batch_generate_videos_captures_success_and_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async def fake_generate_video_tool(**kwargs: Any) -> dict[str, Any]:
        prompt = kwargs["prompt"]
        if "fail" in prompt:
            raise RuntimeError("boom")
        video_path = tmp_path / f"{prompt}.mp4"
        video_path.write_bytes(b"video")
        return {
            "success": True,
            "interaction_id": f"id-{prompt}",
            "video": {"path": str(video_path), "size": 5},
            "metadata": {"task": kwargs["task"]},
        }

    monkeypatch.setattr(batch_module, "generate_video_tool", fake_generate_video_tool)
    monkeypatch.setattr(
        batch_module,
        "get_settings",
        lambda: type("Settings", (), {"api": type("API", (), {"max_batch_size": 2})()})(),
    )

    result = await batch_module.batch_generate_videos(
        ["one", "fail", "two"],
        task="text_to_video",
        batch_size=2,
    )

    assert result["completed"] == 2
    assert result["failed"] == 1
    assert result["results"][0]["interaction_id"] == "id-one"
    assert result["results"][1]["success"] is False
    assert result["results"][2]["interaction_id"] == "id-two"
