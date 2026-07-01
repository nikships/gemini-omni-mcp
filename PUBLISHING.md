# Publishing

Publishing is automated through GitHub Actions (`.github/workflows/publish.yml`). Every push to `main` bumps the version, tags, builds, uploads to PyPI, and creates a GitHub release.

## Version bumping

The bump type is read from the last commit message:

| Commit message | Bump | Example |
|----------------|------|---------|
| `Fix polling timeout` | Patch | `1.0.0` -> `1.0.1` |
| `[minor] Add reference video tool` | Minor | `1.0.0` -> `1.1.0` |
| `[major] Breaking tool parameter changes` | Major | `1.0.0` -> `2.0.0` |

Add `[skip ci]` to a commit message to push without publishing (docs, README, etc.).

You can also trigger a release manually: Actions -> Publish to PyPI -> Run workflow, and pick the bump type.

## Setup requirements

- `PYPI_API_TOKEN` repository secret with upload permissions for `gemini-omni-mcp`.

## Local validation

```bash
uv sync --all-extras
uv run ruff format --check .
uv run ruff check .
uv run mypy gemini_omni_mcp/
uv run pytest
uv build
```

## Verifying publication

1. Check PyPI: https://pypi.org/project/gemini-omni-mcp/
2. Check releases: https://github.com/nikships/gemini-omni-mcp/releases
3. Test install: `pip install gemini-omni-mcp --upgrade` or `uvx gemini-omni-mcp`
