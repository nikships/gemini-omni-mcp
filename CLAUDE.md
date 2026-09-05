# Gemini Omni MCP development notes

This repository is a FastMCP server for `gemini-omni-1.1-flash` video generation through the Google GenAI SDK Interactions API.

## Commands

```bash
uv sync --all-extras
uv run ruff format .
uv run ruff check .
uv run mypy gemini_omni_mcp/
uv run pytest
uv build
```

## API notes

- Use `client.aio.interactions.create` for generation and editing.
- Use `response_format={"type":"video","aspect_ratio":"16:9"|"9:16","resolution":"360p"|"720p"|"1080p"|"4k","delivery":"uri"|"inline"}`.
- Use `generation_config={"video_config":{"task": ...}}` for `text_to_video`, `image_to_video`, `reference_to_video`, and `extend` with uploaded videos. Omit it for `edit` and multi-turn `extend`: the API rejects `previous_interaction_id` together with an explicit task, so those are prompt-based.
- Prefer `delivery="uri"`, then poll `client.aio.files.get(name="files/{id}")` until `ACTIVE`, then call `client.aio.files.download(file=uri)`.
- Preserve `store=True` so `previous_interaction_id` can edit generated videos.
- Never commit `.env`, API keys, or generated MP4 test artifacts unless explicitly requested.
