# CLAUDE.md

FastAPI service that accepts call center transcripts, returns structured QA analysis via the Claude API, and persists results to MongoDB.

**Package manager:** `uv`

## Commands

```bash
uv sync                               # install all deps (including dev)
uv run pre-commit install             # install git hooks (once after cloning)
uv run uvicorn app.main:app --reload  # dev server on :8000
uv run pytest                         # run tests
uv run ruff check .                   # lint
uv run ruff format .                  # format
```

**Before every commit:** `uv run ruff check .` and `uv run ruff format --check .` must pass. Pre-commit hooks enforce this automatically.

## Required environment variables

- `ANTHROPIC_API_KEY` — required; app fails to start without it
- `MONGODB_URL` — optional; default `mongodb://localhost:27017`
- `MONGODB_DB_NAME` — optional; default `transcript_analysis`

Copy `.env.example` to `.env` and set `ANTHROPIC_API_KEY`.

## References

- [Architecture](.agents/architecture.md) — domain layout, MongoDB setup, dependency injection
- [Testing](.agents/testing.md) — async test pattern, Claude API mock, repository mock
- [Style guide](.agents/style-guide.md) — ruff rules, pre-commit, CI
- [Docker](.agents/docker.md) — Dockerfile, docker-compose with MongoDB
- [API design](.agents/api-design.md) — error codes, pagination, Claude API patterns
- [API: transcripts](docs/specs/analyze-transcript.md) — `POST /transcripts/analyze`
- [API: persistence](docs/specs/persistence.md) — `GET /transcripts/`, `GET /transcripts/{id}`
- [API: topic search](docs/specs/topic-search.md) — `GET /transcripts/topics`, `POST /transcripts/search`
