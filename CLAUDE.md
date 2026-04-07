# CLAUDE.md

Stateless FastAPI service that accepts call center transcripts and returns structured QA analysis via the Claude API.

**Package manager:** `uv`

## Commands

```bash
uv sync                                   # install all deps (including dev)
uv run pre-commit install                 # install git hooks (once after cloning)
uv run uvicorn app.main:app --reload      # dev server on :8000
uv run pytest                             # run tests
uv run ruff check .                       # lint
uv run ruff format .                      # format
```

**Before every commit:** `uv run ruff check .` and `uv run ruff format --check .` must pass. Pre-commit hooks enforce this automatically.

## Required environment variable

`ANTHROPIC_API_KEY` — the app fails to start without it. Copy `.env.example` to `.env` and set it.

## References

- [Architecture](.agents/architecture.md) — domain layout, router registration, config, dependency injection
- [Testing](.agents/testing.md) — async test pattern (pytest-anyio), Claude API mock pattern
- [Style guide](.agents/style-guide.md) — ruff rules, pre-commit, CI
- [Docker](.agents/docker.md) — Dockerfile, docker-compose, layer caching
- [API spec](docs/specs/analyze-transcript.md) — `POST /transcripts/analyze` request/response contract
