from pathlib import Path

import pytest

from gemini_omni_mcp.config.constants import (
    DELIVERY_OPTIONS,
    MAX_PROMPT_LENGTH,
    OMNI_TASKS,
    VIDEO_ASPECT_RATIOS,
)
from gemini_omni_mcp.core.exceptions import ValidationError
from gemini_omni_mcp.core.validation import (
    coerce_image_paths,
    validate_batch_size,
    validate_delivery,
    validate_duration_seconds,
    validate_input_video,
    validate_model,
    validate_prompt,
    validate_prompts_list,
    validate_task,
    validate_video_aspect_ratio,
)


@pytest.mark.unit
class TestValidation:
    @pytest.mark.parametrize("aspect_ratio", VIDEO_ASPECT_RATIOS)
    def test_validate_video_aspect_ratio_valid(self, aspect_ratio: str) -> None:
        assert validate_video_aspect_ratio(aspect_ratio) == aspect_ratio

    @pytest.mark.parametrize("invalid_ratio", ["1:1", "4:5", "invalid", ""])
    def test_validate_video_aspect_ratio_invalid(self, invalid_ratio: str) -> None:
        with pytest.raises(ValidationError) as excinfo:
            validate_video_aspect_ratio(invalid_ratio)
        assert f"Invalid aspect ratio '{invalid_ratio}'" in str(excinfo.value)

    @pytest.mark.parametrize("task", OMNI_TASKS)
    def test_validate_task_valid(self, task: str) -> None:
        assert validate_task(task) == task

    def test_validate_task_empty(self) -> None:
        assert validate_task(None) is None
        assert validate_task("") is None

    def test_validate_task_invalid(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            validate_task("animate")
        assert "Invalid task" in str(excinfo.value)

    @pytest.mark.parametrize("duration", [3, 5, 10])
    def test_validate_duration_valid(self, duration: int) -> None:
        assert validate_duration_seconds(duration) == duration

    @pytest.mark.parametrize("duration", [0, 2, 11])
    def test_validate_duration_invalid_range(self, duration: int) -> None:
        with pytest.raises(ValidationError) as excinfo:
            validate_duration_seconds(duration)
        assert "duration_seconds must be between" in str(excinfo.value)

    def test_validate_duration_invalid_type(self) -> None:
        with pytest.raises(ValidationError):
            validate_duration_seconds("5")  # type: ignore[arg-type]

    @pytest.mark.parametrize("delivery", DELIVERY_OPTIONS)
    def test_validate_delivery_valid(self, delivery: str) -> None:
        assert validate_delivery(delivery) == delivery

    def test_validate_delivery_invalid(self) -> None:
        with pytest.raises(ValidationError):
            validate_delivery("download")

    @pytest.mark.parametrize("prompt", ["Valid prompt", "A" * MAX_PROMPT_LENGTH])
    def test_validate_prompt_valid(self, prompt: str) -> None:
        validate_prompt(prompt)

    @pytest.mark.parametrize(
        "invalid_prompt,expected",
        [
            ("", "Prompt cannot be empty"),
            ("   ", "Prompt cannot be empty"),
            ("A" * (MAX_PROMPT_LENGTH + 1), "Prompt too long"),
        ],
    )
    def test_validate_prompt_invalid(self, invalid_prompt: str, expected: str) -> None:
        with pytest.raises(ValidationError) as excinfo:
            validate_prompt(invalid_prompt)
        assert expected in str(excinfo.value)

    @pytest.mark.parametrize("model", ["gemini-omni-flash-preview", "gemini-flash-latest"])
    def test_validate_model_valid(self, model: str) -> None:
        validate_model(model)

    def test_validate_model_invalid(self) -> None:
        with pytest.raises(ValidationError):
            validate_model("non-existent-model")

    @pytest.mark.parametrize("size,max_size", [(1, 4), (3, 4), (4, 4)])
    def test_validate_batch_size_valid(self, size: int, max_size: int) -> None:
        validate_batch_size(size, max_size)

    @pytest.mark.parametrize("size,max_size", [(0, 4), (-1, 4), (5, 4), ("1", 4)])
    def test_validate_batch_size_invalid(self, size: object, max_size: int) -> None:
        with pytest.raises(ValidationError):
            validate_batch_size(size, max_size)  # type: ignore[arg-type]

    def test_validate_prompts_list(self) -> None:
        validate_prompts_list(["one", "two"])
        with pytest.raises(ValidationError):
            validate_prompts_list([])


@pytest.mark.unit
class TestCoerceImagePaths:
    def test_none_and_empty(self) -> None:
        assert coerce_image_paths(None) is None
        assert coerce_image_paths("") is None
        assert coerce_image_paths("   ") is None

    def test_single_path_string(self) -> None:
        assert coerce_image_paths("/a.png") == ["/a.png"]
        assert coerce_image_paths("  /x y.png  ") == ["/x y.png"]

    def test_json_encoded_list_string(self) -> None:
        assert coerce_image_paths('["/a.png", "/b.png"]') == ["/a.png", "/b.png"]

    def test_malformed_json_treated_as_path(self) -> None:
        assert coerce_image_paths("[not json") == ["[not json"]

    def test_existing_list_passthrough(self) -> None:
        assert coerce_image_paths(["/a.png", "/b.png"]) == ["/a.png", "/b.png"]


@pytest.mark.unit
class TestInputVideoValidation:
    def test_validate_input_video_valid(self, tmp_path: Path) -> None:
        video = tmp_path / "input.mp4"
        video.write_bytes(b"video")
        assert validate_input_video(video) == video.resolve()

    def test_validate_input_video_rejects_extension(self, tmp_path: Path) -> None:
        video = tmp_path / "input.mov"
        video.write_bytes(b"video")
        with pytest.raises(ValidationError):
            validate_input_video(video)

    def test_validate_input_video_rejects_empty(self, tmp_path: Path) -> None:
        video = tmp_path / "input.mp4"
        video.write_bytes(b"")
        with pytest.raises(ValidationError):
            validate_input_video(video)
