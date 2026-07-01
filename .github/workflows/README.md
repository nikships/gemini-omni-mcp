# Workflows

- `test.yml`: runs formatting, linting, type checking, tests, build, and import smoke tests.
- `publish.yml`: on push to `main` (or manual dispatch) bumps version, tags, builds, publishes to PyPI, and creates a GitHub release. Use `[minor]`/`[major]` in the commit message to control the bump; `[skip ci]` skips publishing.
