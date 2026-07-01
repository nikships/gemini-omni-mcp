# Gemini Omni MCP

FastMCP server for Google's `gemini-omni-flash-preview` video model. It supports text-to-video, image-to-video, multiple reference images, uploaded-video edits, stateful edits with `previous_interaction_id`, URI delivery, inline delivery, and batch generation.

## Install

```bash
uvx gemini-omni-mcp
```

Or from source:

```bash
uv sync --all-extras
uv run gemini-omni-mcp
```

## Configuration

```bash
export GEMINI_API_KEY=your_key_here
export OUTPUT_DIR=~/gemini_omni_videos
```

Optional settings include `REQUEST_TIMEOUT`, `FILE_POLL_INTERVAL`, `FILE_POLL_TIMEOUT`, `MAX_BATCH_SIZE`, `DEFAULT_ASPECT_RATIO`, `DEFAULT_DELIVERY`, and `DEFAULT_DURATION_SECONDS`.

## Tools

### `generate_video`

Generates one MP4 and returns JSON with `video.path`, `interaction_id`, and metadata.

Important arguments:

- `prompt`: scene, motion, camera, lighting, mood, and audio direction
- `task`: `text_to_video`, `image_to_video`, `reference_to_video`, or `edit`
- `aspect_ratio`: `16:9` or `9:16`
- `duration_seconds`: optional preview field, `3` to `10`
- `reference_image_paths`: up to 6 local image paths
- `input_video_path`: local MP4 to upload and edit
- `delivery`: `uri` or `inline`
- `previous_interaction_id`: continue editing a generated video

### `batch_generate`

Runs multiple prompts in conservative parallel batches, capped at 4.

## Prompting tips

- Use "single continuous shot" and "no scene cuts" for one-scene outputs.
- Include audio direction, for example "gentle ambient sound, no dialogue".
- For edits, keep the prompt short and add "Keep everything else the same".
- Use `<FIRST_FRAME>` and `<IMAGE_REF_N>` tags to bind reference-image roles.
- Timing cues like `[0-3s]`, `[3-6s]`, and `[6-10s]` work well.

## Development

```bash
uv sync --all-extras
uv run ruff format .
uv run ruff check .
uv run mypy gemini_omni_mcp/
uv run pytest
uv build
```
