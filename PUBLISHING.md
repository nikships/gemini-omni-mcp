# Publishing

1. Run validators:

```bash
uv sync --all-extras
uv run ruff format --check .
uv run ruff check .
uv run mypy gemini_omni_mcp/
uv run pytest
uv build
```

2. Tag and publish through the GitHub Actions publish workflow, or upload `dist/*` to PyPI with Twine.
