"""MCP prompt templates for Gemini Omni Flash video generation."""

from typing import Any

from ..config.constants import MAX_BATCH_SIZE


def register_video_prompts(mcp_server: Any) -> None:
    """Register video-generation prompt templates with the MCP server."""

    @mcp_server.prompt()
    def continuous_cinematic_scene(
        subject: str,
        setting: str,
        camera_motion: str = "slow dolly forward",
        audio: str = "natural ambient sound, no dialogue",
    ) -> str:
        """Single-shot cinematic scene prompt for generate_video."""
        prompt = (
            f"Single continuous shot, no scene cuts. {subject} in {setting}. "
            f"Camera movement: {camera_motion}. Rich natural motion, cinematic lighting, "
            f"clear subject detail, atmospheric depth. Sound design: {audio}."
        )
        return f"Call `generate_video` with prompt: {prompt!r}, task: 'text_to_video', aspect_ratio: '16:9'."

    @mcp_server.prompt()
    def image_to_video_motion(
        subject_motion: str,
        camera_motion: str = "gentle handheld push-in",
        audio: str = "soft ambience, no dialogue",
    ) -> str:
        """Reference-image motion prompt for generate_video."""
        prompt = (
            f"<FIRST_FRAME> Single continuous shot. Animate the provided image with {subject_motion}. "
            f"Camera movement: {camera_motion}. Keep identity, clothing, and environment consistent. "
            f"Sound design: {audio}."
        )
        return (
            "Call `generate_video` with the prompt below, task: 'image_to_video', "
            f"and reference_image_paths set to the user's image path. Prompt: {prompt!r}"
        )

    @mcp_server.prompt()
    def timed_sequence(concept: str, aspect_ratio: str = "16:9") -> str:
        """Timed 10-second sequence prompt."""
        prompt = (
            f"[0-3s] Establish {concept} in a vivid cinematic wide shot. "
            "[3-6s] Camera moves closer as the main action begins. "
            "[6-10s] The action resolves with a memorable final frame. "
            "Cohesive lighting, smooth transitions, expressive sound design, no dialogue."
        )
        return (
            "Call `generate_video` with "
            f"prompt: {prompt!r}, aspect_ratio: {aspect_ratio!r}, duration_seconds: 10."
        )

    @mcp_server.prompt()
    def edit_instruction(change: str) -> str:
        """Simple video-edit prompt for previous_interaction_id workflows."""
        prompt = f"{change}. Keep everything else the same."
        return (
            "Call `generate_video` with task: 'edit', previous_interaction_id set to the prior "
            f"interaction id, and prompt: {prompt!r}."
        )

    @mcp_server.prompt()
    def batch_storyboard(concept: str, num_scenes: int = 4) -> str:
        """Storyboard prompt list for batch_generate."""
        num_scenes = min(num_scenes, MAX_BATCH_SIZE)
        prompts = [
            f"Single continuous shot, no scene cuts. Scene {i + 1} of {concept}. "
            "Distinct camera angle and motion, clear action, cinematic lighting, natural audio."
            for i in range(num_scenes)
        ]
        return f"Call `batch_generate` with prompts: {prompts!r}, aspect_ratio: '16:9'."

    _registered_prompts = (
        continuous_cinematic_scene,
        image_to_video_motion,
        timed_sequence,
        edit_instruction,
        batch_storyboard,
    )
    del _registered_prompts
