from pathlib import Path

import pytest

from gemini_omni_mcp.services.video_service import VideoResult


@pytest.mark.unit
def test_video_result_save(tmp_path: Path) -> None:
    result = VideoResult(
        video_bytes=b"mp4 bytes",
        prompt="A cinematic test video",
        model="gemini-omni-flash-preview",
        interaction_id="v1_test",
    )

    output = result.save(tmp_path)

    assert output.suffix == ".mp4"
    assert output.read_bytes() == b"mp4 bytes"
    assert result.get_size() == len(b"mp4 bytes")


@pytest.mark.unit
def test_video_result_save_custom_filename(tmp_path: Path) -> None:
    result = VideoResult(b"video", "prompt", "gemini-omni-flash-preview")

    output = result.save(tmp_path, "custom.mp4")

    assert output == tmp_path / "custom.mp4"
    assert output.read_bytes() == b"video"
