"""Optional prompt enhancement service for Gemini Omni Flash video."""

import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class TextGenerator(Protocol):
    """Protocol for text-generation clients used by prompt enhancement."""

    async def generate_text(
        self,
        prompt: str,
        *,
        model: str = "gemini-flash-latest",
        system_instruction: str | None = None,
    ) -> str: ...


PROMPT_ENHANCEMENT_SYSTEM_INSTRUCTION = """You are an expert prompt engineer for Gemini Omni Flash video generation.

Enhance video prompts while preserving the user's intent. Prefer concise, production-ready language:
1. Describe one continuous scene unless the user asks for cuts.
2. Include camera movement, subject motion, lighting, mood, and environment.
3. Include sound design or music direction when useful.
4. Use timing cues like [0-3s], [3-6s], or natural language timing only when helpful.
5. For edits, keep the prompt simple and include "Keep everything else the same".
6. For image inputs, use <FIRST_FRAME> or <IMAGE_REF_N> tags only if the role is clear.
7. Avoid unsupported knobs such as system instructions, negative_prompt, temperature, top_p, or stop sequences.
8. Output only the enhanced prompt, no explanations."""


class PromptEnhancer:
    """Enhances video generation prompts using Gemini Flash."""

    def __init__(self, gemini_client: TextGenerator) -> None:
        self.gemini_client = gemini_client

    async def enhance_prompt(
        self,
        original_prompt: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """Enhance a prompt for better video generation results."""
        instruction = self._build_enhancement_instruction(original_prompt, context)

        try:
            enhanced = await self.gemini_client.generate_text(
                prompt=instruction,
                system_instruction=PROMPT_ENHANCEMENT_SYSTEM_INSTRUCTION,
                model="gemini-flash-latest",
            )
            enhanced = enhanced.strip()
            logger.info("Prompt enhanced: %s -> %s chars", len(original_prompt), len(enhanced))
            return {"original_prompt": original_prompt, "enhanced_prompt": enhanced}
        except Exception as e:
            logger.warning("Prompt enhancement failed, using original: %s", e)
            return {"original_prompt": original_prompt, "enhanced_prompt": original_prompt}

    def _build_enhancement_instruction(self, prompt: str, context: dict[str, Any] | None) -> str:
        """Compose the enhancement instruction from the prompt and optional hints."""
        parts = [f"Enhance this Gemini Omni Flash video prompt:\n\n{prompt}"]
        if context:
            if context.get("is_editing"):
                parts.append(
                    "\nContext: This is for video editing. Keep edits simple and preserve all "
                    "unstated details."
                )
            if context.get("has_reference_images"):
                parts.append(
                    "\nContext: Reference images are provided. Assign roles with <FIRST_FRAME> "
                    "or <IMAGE_REF_N> tags only when it improves clarity."
                )
            ratio = context.get("aspect_ratio")
            if ratio == "16:9":
                parts.append("\nFormat: Landscape video.")
            elif ratio == "9:16":
                parts.append("\nFormat: Portrait vertical video.")
        return "\n".join(parts)


async def create_prompt_enhancer(api_key: str, timeout: int = 30) -> PromptEnhancer:
    """Create a standalone PromptEnhancer."""
    from .gemini_client import GeminiVideoClient

    return PromptEnhancer(GeminiVideoClient(api_key=api_key, timeout=timeout))
